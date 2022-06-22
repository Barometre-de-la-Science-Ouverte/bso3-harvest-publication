import gzip
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from time import time
from typing import List

import requests
from grobid_client.grobid_client import GrobidClient
from software_mentions_client.client import software_mentions_client as smc

from application.server.main.logger import get_logger
from config.db_config import engine
from config.harvester_config import config_harvester
from config.logger_config import LOGGER_LEVEL
from config.path_config import (CONFIG_PATH_GROBID, CONFIG_PATH_SOFTCITE,
                                DESTINATION_DIR_METADATA,
                                PUBLICATIONS_DOWNLOAD_DIR)
from harvester.OAHarvester import OAHarvester
from infrastructure.database.db_handler import DBHandler
from infrastructure.storage.swift import Swift
from load_metadata import load_metadata
from ovh_handler import download_files, upload_and_clean_up
from run_grobid import run_grobid
from run_softcite import run_softcite

METADATA_DUMP = config_harvester['metadata_dump']
logger_console = get_logger(__name__, level=LOGGER_LEVEL)


def create_task_harvest_partition(source_metadata_file, partition_index, total_partition_number, doi_list, wiley_client):
    swift_handler = Swift(config_harvester)
    db_handler = DBHandler(engine=engine, table_name='harvested_status_table', swift_handler=swift_handler)

    source_metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                         metadata_file=source_metadata_file,
                                         destination_dir=DESTINATION_DIR_METADATA)
    partition_size = get_partition_size(source_metadata_file, total_partition_number)
    filtered_metadata_filename = os.path.join(os.path.dirname(source_metadata_file),
                                              'filtered_' + os.path.basename(source_metadata_file))
    write_partitioned_metadata_file(source_metadata_file, filtered_metadata_filename, partition_size, partition_index)
    write_partitioned_filtered_metadata_file(db_handler, filtered_metadata_filename, filtered_metadata_filename,
                                             doi_list)
    harvester = OAHarvester(config_harvester, wiley_client)
    harvester.harvestUnpaywall(filtered_metadata_filename)
    harvester.diagnostic()
    logger_console.debug(f'{db_handler.count()} rows in database before harvesting')
    db_handler.update_database()
    logger_console.debug(f'{db_handler.count()} rows in database after harvesting')
    harvester.reset_lmdb()

def create_task_unpaywall(args):
    logger_console.debug(f'launching task with args {args}')
    sample_seed = args.get('sample_seed', 1)
    nb_samples = args.get('nb_samples', -1)
    metadata_file = args.get('metadata_file', '')
    metadata_folder = args.get('metadata_folder', '')

    swift_handler = Swift(config_harvester)
    db_handler: DBHandler = DBHandler(engine=engine, table_name='harvested_status_table', swift_handler=swift_handler)
    logger_console.debug('Database before harvesting')
    logger_console.debug(db_handler.fetch_all())
    if ((metadata_file == '') and (metadata_folder == '')) or ((metadata_file != '') and (metadata_folder != '')):
        logger_console.debug(f'Only one of the two arguments metadata_file of metadata_folder should be provided!')
    else:
        if metadata_folder:
            logger_console.debug(f'Metadata folder provided : {metadata_folder}')
            list_local_files = []
            files = swift_handler.get_swift_list(container=METADATA_DUMP, dir_name=metadata_folder)
            for file in files:
                metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                              metadata_file=file,
                                              destination_dir=DESTINATION_DIR_METADATA,
                                              subfolder_name=metadata_folder)
                list_local_files.append(metadata_file)
                logger_console.debug(f'Metadata list files after metadata folder provided: {list_local_files}')
        else:
            metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                          metadata_file=metadata_file,
                                          destination_dir=DESTINATION_DIR_METADATA)
            list_local_files = [metadata_file]
            logger_console.debug(f'Metadata file provided: {metadata_file}')
            logger_console.debug(f'Metadata list files after metadata file provided: {list_local_files}')

        for file in list_local_files:
            if metadata_folder:
                end_file_name = os.path.basename(file)
                file_generic_name = end_file_name.split('.')[0]
                destination_dir_output = os.path.join(metadata_folder, file_generic_name)
                logger_console.debug(f'destination dir output (folder statement): {destination_dir_output}')
            else:
                destination_dir_output = ''
                logger_console.debug(f'destination dir output (file statement): {destination_dir_output}')
            harvester = OAHarvester(config_harvester, sample=nb_samples, sample_seed=sample_seed)
            logger_console.debug(f'metadata file in harvest unpaywall : {file}')
            logger_console.debug(f'metadata folder in harvest unpaywall : {destination_dir_output}')
            with gzip.open(file, 'rt') as f:
                logger_console.debug("doi in metadata file")
                logger_console.debug([json.loads(line)['doi'] for line in f.readlines()])
            harvester.harvestUnpaywall(file, destination_dir=destination_dir_output)
            harvester.diagnostic()
        try:
            db_handler.update_database()
            harvester.reset_lmdb()
        except Exception as e:
            logger_console.debug(e)
        logger_console.debug('Database after harvesting')
        logger_console.debug(db_handler.fetch_all())


def get_softcite_version(local_files):
    softcite_files = [file for file in local_files if file.endswith('.software.json')]
    if softcite_files:
        with open(softcite_files[0], 'r') as f:
            softcite_version = json.load(f)['version']
    else:
        softcite_version = "0"
    return softcite_version


def get_grobid_version(local_files):
    grobid_files = [file for file in local_files if file.endswith('.tei.xml')]
    if grobid_files:
        with open(CONFIG_PATH_GROBID, 'r') as f:
            config = json.load(f)
        url = f"http://{config['grobid_server']}:{config['grobid_port']}/api/version"
        grobid_version = requests.get(url).text
    else:
        grobid_version = "0"
    return grobid_version


def filter_publications(db_handler, spec_softcite_version, spec_grobid_version):
    entries_publications_grobid = []
    entries_publications_softcite = []
    for record in db_handler.fetch_all():
        uuid, doi = record[1], record[0]
        softcite_version, grobid_version = record[3], record[4]
        if softcite_version != spec_softcite_version:
            entries_publications_softcite.append((doi, uuid))
        if grobid_version != spec_grobid_version:
            entries_publications_grobid.append((doi, uuid))
    return entries_publications_softcite, entries_publications_grobid


def create_task_process(files, spec_grobid_version, spec_softcite_version):
    logger_console.debug(f"Call with args: {files, spec_grobid_version, spec_softcite_version}")
    _swift = Swift(config_harvester)
    db_handler: DBHandler = DBHandler(engine=engine, table_name='harvested_status_table', swift_handler=_swift)
    entries_publications_softcite, entries_publications_grobid = filter_publications(db_handler, spec_softcite_version,
                                                                                     spec_grobid_version)
    publications_grobid = [file for file in files if
                           db_handler._get_uuid_from_path(file) in [e[1] for e in entries_publications_grobid]]
    publications_softcite = [file for file in files if
                             db_handler._get_uuid_from_path(file) in [e[1] for e in entries_publications_softcite]]
    files_to_process = list(set(publications_softcite + publications_grobid))
    download_files(_swift, PUBLICATIONS_DOWNLOAD_DIR, files_to_process)
    start_time = time()
    processing_futures = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        if publications_grobid:
            processing_futures.append(
                executor.submit(run_grobid, CONFIG_PATH_GROBID, PUBLICATIONS_DOWNLOAD_DIR, GrobidClient))
        if publications_softcite:
            processing_futures.append(
                executor.submit(run_softcite, CONFIG_PATH_SOFTCITE, PUBLICATIONS_DOWNLOAD_DIR, smc))
    for future in processing_futures:
        future.result()
    total_time = time()
    logger_console.info(f"Total runtime: {round(total_time - start_time, 3)}s for {len(files)} files")

    local_files = glob(PUBLICATIONS_DOWNLOAD_DIR + '*')
    grobid_uuids = [db_handler._get_uuid_from_path(file) for file in local_files if file.endswith('.tei.xml')]
    softcite_uuids = [db_handler._get_uuid_from_path(file) for file in local_files if file.endswith('.software.json')]
    entries_publications_softcite = [entry for entry in entries_publications_softcite if entry[1] in softcite_uuids]
    entries_publications_grobid = [entry for entry in entries_publications_grobid if entry[1] in grobid_uuids]

    softcite_version = get_softcite_version(local_files)
    grobid_version = get_grobid_version(local_files)
    upload_and_clean_up(_swift, PUBLICATIONS_DOWNLOAD_DIR)
    try:
        db_handler.update_database_processing(list(set(entries_publications_softcite + entries_publications_grobid)),
                                              grobid_version, softcite_version)  # update database
    except Exception:
        logger_console.exception(exc_info=True)


def create_task_prepare_harvest(doi_list, source_metadata_file, filtered_metadata_filename, force):
    logger_console.debug(f'doi_list {doi_list}')
    logger_console.debug(f'filtered_metadata_filename {filtered_metadata_filename}')
    logger_console.debug(f'force {force}')
    swift_handler = Swift(config_harvester)
    db_handler: DBHandler = DBHandler(engine=engine, table_name='harvested_status_table', swift_handler=swift_handler)
    if not force:  # don't redo the ones already done
        doi_already_harvested = [entry[0] for entry in db_handler.fetch_all()]
        doi_list = [doi for doi in doi_list if doi not in doi_already_harvested]
    source_metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                         metadata_file=source_metadata_file,
                                         destination_dir=DESTINATION_DIR_METADATA)
    with gzip.open(source_metadata_file, 'rt') as f_in:
        content = [json.loads(line) for line in f_in.readlines()]
    with gzip.open(os.path.join(DESTINATION_DIR_METADATA, filtered_metadata_filename), 'wt') as f_out:
        f_out.write(os.linesep.join([json.dumps(entry) for entry in content if entry['doi'] in doi_list]))


def get_partition_size(source_metadata_file, total_partition_number):
    with gzip.open(source_metadata_file, 'rt') as f:
        number_of_lines = len(f.readlines())
    partition_size = (number_of_lines // total_partition_number)
    return partition_size


def write_partitioned_metadata_file(source_metadata_file: str, filtered_metadata_filename: str, partition_size: int,
                                    partition_index: int):
    with gzip.open(source_metadata_file, 'rt') as f_in:
        with gzip.open(filtered_metadata_filename, 'wt') as f_out:
            content = f_in.readlines()
            logger_console.debug(f'Number of publications in original file: {len(content)}')
            filtered_file_content = ''.join(
                content[(partition_index * partition_size):((partition_index + 1) * partition_size)])
            logger_console.debug('Number of publications in the partition file: '
                                 + f'{len(content[(partition_index * partition_size):((partition_index + 1) * partition_size)])}')
            f_out.write(filtered_file_content)


def write_partitioned_filtered_metadata_file(db_handler: DBHandler,
                                             source_metadata_file: str, filtered_metadata_filename: str,
                                             doi_list: List[str]) -> None:
    doi_already_harvested_list = [entry[0] for entry in db_handler.fetch_all()]

    with gzip.open(source_metadata_file, 'rt') as f_in:
        metadata_input_file_content_list = [json.loads(line) for line in f_in.readlines()]

    filtered_publications_metadata_json_list = metadata_input_file_content_list
    if len(doi_list) > 0:
        filtered_publications_metadata_json_list = [
            entry for entry in filtered_publications_metadata_json_list \
            if entry['doi'] in doi_list
        ]
    filtered_publications_metadata_json_list = [
        entry for entry in filtered_publications_metadata_json_list \
        if entry['doi'] not in doi_already_harvested_list
    ]
    logger_console.debug(
        f'Number of publications in the file after filtering: {len(filtered_publications_metadata_json_list)}')
    with gzip.open(os.path.join(DESTINATION_DIR_METADATA, filtered_metadata_filename), 'wt') as f_out:
        f_out.write(os.linesep.join([json.dumps(entry) for entry in filtered_publications_metadata_json_list]))


def create_task_clean_up(filtered_metadata_file):
    from config.swift_cli_config import init_cmd
    subprocess.check_call(f'{init_cmd} delete {METADATA_DUMP} {filtered_metadata_file}', shell=True)
