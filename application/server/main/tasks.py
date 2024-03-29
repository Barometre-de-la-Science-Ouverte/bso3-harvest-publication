from asyncio import futures
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from time import time
from typing import List, Tuple

import requests
from grobid_client.grobid_client import GrobidClient
from softdata_mentions_client.client import softdata_mentions_client

from application.server.main.logger import get_logger
from config.db_config import engine
from config.harvester_config import config_harvester
from config.logger_config import LOGGER_LEVEL
from config.path_config import DESTINATION_DIR_METADATA
from config.processing_service_namespaces import ServiceNamespace, grobid_ns, softcite_ns, datastet_ns
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


def compile_records_for_db(service_ns: ServiceNamespace, db_handler: DBHandler) -> List[Tuple[str,str,str]]:
    """List the output files of a service to determine what to update in db.
    Returns [(uuid, service, version), ...]"""
    local_files = glob(service_ns.dir + '*')
    service_version = get_service_version(service_ns.suffix, local_files)
    processed_publications = [
        (db_handler._get_uuid_from_path(file), service_ns.service_name, service_version)
        for file in local_files if file.endswith(service_ns.suffix)
    ]
    return processed_publications


def run_processing_services():
    """Run parallel calls to the different services when there are files to process"""
    processing_futures = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        if next(iter(glob(grobid_ns.dir + '*')), None):
            processing_futures.append(
                executor.submit(run_grobid, None, grobid_ns.dir, GrobidClient))
        if next(iter(glob(softcite_ns.dir + '*')), None):
            processing_futures.append(
                executor.submit(run_softcite, None, softcite_ns.dir, softdata_mentions_client))
        if next(iter(glob(datastet_ns.dir + '*')), None):
            processing_futures.append(
                executor.submit(run_datastet, None, datastet_ns.dir, softdata_mentions_client))
    for future in processing_futures:
        future.result()


def create_task_process(grobid_partition_files, softcite_partition_files, datastet_partition_files):
    logger_console.debug(f"Call with args: {grobid_partition_files, softcite_partition_files, datastet_partition_files}")
    _swift = Swift(config_harvester)
    db_handler: DBHandler = DBHandler(engine=engine, table_name='harvested_status_table', swift_handler=_swift)

    services_ns = [grobid_ns, softcite_ns, datastet_ns]
    list_partition_files = [grobid_partition_files, softcite_partition_files, datastet_partition_files]
    for service_ns, partition_files in zip(services_ns, list_partition_files):
        download_files(_swift, service_ns.dir, partition_files)

    start_time = time()
    run_processing_services()
    total_time = time()
    logger_console.info(f"Total runtime: {round(total_time - start_time, 3)}s for {max(map(len, list_partition_files))} files")


    for service_ns in services_ns:
        entries_to_update = compile_records_for_db(service_ns, db_handler)
        upload_and_clean_up(_swift, service_ns)
        db_handler.update_database_processing(entries_to_update)


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

    # TODO if publication without doi
    # filtered_publications_metadata_json_list = [entry for entry in metadata_input_file_content_list if entry.get('doi') else {'doi': entry['id'], **entry}]
    # instead of:
    filtered_publications_metadata_json_list = metadata_input_file_content_list
    if len(doi_list) > 0:
        filtered_publications_metadata_json_list = [
            entry for entry in filtered_publications_metadata_json_list if entry.get('doi') in doi_list
        ]
    filtered_publications_metadata_json_list = [
        entry for entry in filtered_publications_metadata_json_list if (entry.get('doi') not in doi_already_harvested_list) and entry.get('doi')
    ]
    logger_console.debug(
        f'Number of publications in the file after filtering: {len(filtered_publications_metadata_json_list)}')
    with gzip.open(os.path.join(DESTINATION_DIR_METADATA, filtered_metadata_filename), 'wt') as f_out:
        f_out.write(os.linesep.join([json.dumps(entry) for entry in filtered_publications_metadata_json_list]))
