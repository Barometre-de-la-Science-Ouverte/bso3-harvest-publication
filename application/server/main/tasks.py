import gzip
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from time import time
from typing import List, Tuple
from types import SimpleNamespace

import requests
from grobid_client.grobid_client import GrobidClient
from softdata_mentions_client.client import softdata_mentions_client

from application.server.main.logger import get_logger
from config.db_config import engine
from config.harvester_config import config_harvester
from config.logger_config import LOGGER_LEVEL
from config.path_config import DESTINATION_DIR_METADATA
from config.processing_service_namespaces import grobid_ns, softcite_ns, datastet_ns
from harvester.OAHarvester import OAHarvester
from infrastructure.database.db_handler import DBHandler
from infrastructure.storage.swift import Swift
from load_metadata import load_metadata
from ovh_handler import download_files, upload_and_clean_up
from run_grobid import run_grobid
from run_softcite import run_softcite
from run_datastet import run_datastet
from domain.processed_entry import ProcessedEntry

METADATA_DUMP = config_harvester['metadata_dump']
logger_console = get_logger(__name__, level=LOGGER_LEVEL)


def create_task_harvest_partition(source_metadata_file, partition_index, total_partition_number, doi_list,
                                  wiley_client, elsevier_client):
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
    harvester = OAHarvester(config_harvester, wiley_client, elsevier_client)
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
        logger_console.debug('Only one of the two arguments metadata_file of metadata_folder should be provided!')
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


def get_softdata_version(softdata_file_path: str) -> str:
    """Get the version of softcite or datastet used by reading from an output file"""
    with open(softdata_file_path, 'r') as f:
        softdata_version = json.load(f)['version']
    return softdata_version


def get_grobid_version() -> str:
    """Get the version of grobid used by a request to the grobid route /api/version"""
    with open(grobid_ns.config_path, 'r') as f:
        config = json.load(f)
    url = f"http://{config['grobid_server']}:{config['grobid_port']}/api/version"
    grobid_version = requests.get(url).text
    return grobid_version


def get_publications_entries_to_process(db_records: List[ProcessedEntry], service_name: str, min_spec_version: str) -> List[ProcessedEntry]:
    """Return all the publications in the database that needs to be processed by a service (i.e. not just for the partition)"""
    publications_entries_to_process = []

    for record in db_records:
        if service_name == datastet_ns.service_name:
            current_version = record.datastet_version
        elif service_name == softcite_ns.service_name:
            current_version = record.softcite_version
        elif service_name == grobid_ns.service_name:
            current_version = record.grobid_version
        if current_version < min_spec_version:
            publications_entries_to_process.append(record)
    return publications_entries_to_process


def get_service_version(file_suffix: str, local_files: List[str]) -> str:
    """Return the version of the service that produced the files"""
    processed_files = [file for file in local_files if file.endswith(file_suffix)]
    if processed_files:
        if file_suffix == datastet_ns.suffix:
            return get_softdata_version(processed_files[0])
        if file_suffix == softcite_ns.suffix:
            return get_softdata_version(processed_files[0])
        elif file_suffix == grobid_ns.suffix:
            return get_grobid_version()
    else:
        return "0"


def compile_records_for_db(entries_to_process: List[ProcessedEntry], service_ns: SimpleNamespace, db_handler: DBHandler) -> List[Tuple[str]]:
    """List the output files of a service to determine what to update in db.
    Returns [(uuid, service, version), ...]"""
    local_files = glob(service_ns.dir + '*')
    processed_uuids = [db_handler._get_uuid_from_path(file) for file in local_files if file.endswith(service_ns.suffix)]
    service_version = get_service_version(service_ns.suffix, local_files)
    processed_publications = [
        (entry.uuid, service_ns.service_name, service_version)
        for entry in entries_to_process if entry.uuid in processed_uuids
    ]
    return processed_publications


def run_processing_services():
    """Run parallel calls to the different services when there are files to process"""
    processing_futures = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        if next(iter(glob(grobid_ns.dir + '*')), None):
            processing_futures.append(
                executor.submit(run_grobid, grobid_ns.config_path, grobid_ns.dir, GrobidClient))
        if next(iter(glob(softcite_ns.dir + '*')), None):
            processing_futures.append(
                executor.submit(run_softcite, softcite_ns.config_path, softcite_ns.dir, softdata_mentions_client))
        if next(iter(glob(datastet_ns.dir + '*')), None):
            processing_futures.append(
                executor.submit(run_datastet, datastet_ns.config_path, datastet_ns.dir, softdata_mentions_client))
    for future in processing_futures:
        future.result()


def create_task_process(partition_files, spec_grobid_version, spec_softcite_version, spec_datastet_version):
    logger_console.debug(f"Call with args: {partition_files, spec_grobid_version, spec_softcite_version, spec_datastet_version}")
    _swift = Swift(config_harvester)
    db_handler: DBHandler = DBHandler(engine=engine, table_name='harvested_status_table', swift_handler=_swift)
    db_records = db_handler.fetch_all()
    services_ns = [grobid_ns, softcite_ns, datastet_ns]
    spec_versions = [spec_grobid_version, spec_softcite_version, spec_datastet_version]
    publications_entries_services = []
    for service_ns, spec_version_service in zip(services_ns, spec_versions):
        publications_entries = get_publications_entries_to_process(db_records, service_ns.service_name, spec_version_service)
        publications_entries_services.append(publications_entries)
        uuids_publications_to_process = [e.uuid for e in publications_entries]
        publication_files = [file for file in partition_files if db_handler._get_uuid_from_path(file) in uuids_publications_to_process]
        if publication_files:
            download_files(_swift, service_ns.dir, publication_files)

    start_time = time()
    run_processing_services()
    total_time = time()
    logger_console.info(f"Total runtime: {round(total_time - start_time, 3)}s for {len(partition_files)} files")


    for service_ns, publications_entries in zip(services_ns, publications_entries_services):
        entries_to_update = compile_records_for_db(publications_entries, service_ns, db_handler)
        upload_and_clean_up(_swift, service_ns)
        db_handler.update_database_processing(entries_to_update)


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
            entry for entry in filtered_publications_metadata_json_list if entry.get('doi') in doi_list
        ]
    filtered_publications_metadata_json_list = [
        entry for entry in filtered_publications_metadata_json_list if entry['doi'] not in doi_already_harvested_list
    ]
    logger_console.debug(
        f'Number of publications in the file after filtering: {len(filtered_publications_metadata_json_list)}')
    with gzip.open(os.path.join(DESTINATION_DIR_METADATA, filtered_metadata_filename), 'wt') as f_out:
        f_out.write(os.linesep.join([json.dumps(entry) for entry in filtered_publications_metadata_json_list]))


def create_task_clean_up(filtered_metadata_file):
    from config.swift_cli_config import init_cmd
    subprocess.check_call(f'{init_cmd} delete {METADATA_DUMP} {filtered_metadata_file}', shell=True)
