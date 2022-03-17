import json
import os
from glob import glob
from time import time

import requests
from application.server.main.logger import get_logger
from grobid_client.grobid_client import GrobidClient
from harvester.OAHarvester import OAHarvester
from infrastructure.database.db_handler import DBHandler
from infrastructure.storage.swift import Swift
from load_metadata import load_metadata
from ovh_handler import download_files, upload_and_clean_up
from run_grobid import run_grobid
from run_softcite import run_softcite
from software_mentions_client.client import software_mentions_client as smc

from config.db_config import engine
from config.harvester_config import config_harvester
from config.logger_config import LOGGER_LEVEL
from config.path_config import (CONFIG_PATH_GROBID, CONFIG_PATH_SOFTCITE,
                                DESTINATION_DIR_METADATA,
                                PUBLICATIONS_DOWNLOAD_DIR)

METADATA_DUMP = config_harvester['metadata_dump']
logger_console = get_logger(__name__, level=LOGGER_LEVEL)


def create_task_unpaywall(args):
    logger_console.debug(f'launching task with args {args}')
    sample_seed = args.get('sample_seed', 1)
    nb_samples = args.get('nb_samples', 1)
    metadata_file = args.get('metadata_file', '')
    metadata_folder = args.get('metadata_folder', '')

    swift_handler = Swift(config_harvester)
    db_handler: DBHandler = DBHandler(engine=engine, table_name='harvested_status_table', swift_handler=swift_handler)

    if ((metadata_file == '') and (metadata_folder == '')) or ((metadata_file != '') and (metadata_folder != '')):
        logger_console.debug(f'Only one of the two arguments metadata_file of metadata_folder should be provided!')
    else:
        if metadata_folder:
            list_local_files = []
            files = swift_handler.get_swift_list(container=METADATA_DUMP, dir_name=metadata_folder)
            for file in files:
                metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                              metadata_file=file,
                                              destination_dir=DESTINATION_DIR_METADATA,
                                              subfolder_name=metadata_folder)
                list_local_files.append(metadata_file)
        else:
            list_local_files = [metadata_file]

        for file in list_local_files:
            if metadata_folder:
                end_file_name = os.path.basename(file)
                file_generic_name = end_file_name.split('.')[0]
                destination_dir_output = os.path.join(metadata_folder, file_generic_name)
            else:
                destination_dir_output=''
            harvester = OAHarvester(config_harvester, thumbnail=False, sample=nb_samples, sample_seed=sample_seed)
            harvester.harvestUnpaywall(file, destination_dir=destination_dir_output)

        try:
            db_handler.update_database()  # update database
        except Exception as e:
            logger_console.debug(e)


def get_softcite_version(local_files):
    softcite_files = [file for file in local_files if file.endswith('.software.json')]
    if softcite_files:
        with open(softcite_files[0], 'r') as f:
            softcite_version = json.load(f)['version']
    else:
        softcite_version = "0"
    return softcite_version

def get_grobid_version(local_files):
    grobid_files = [file for file in local_files if file.endswith('.software.json')]
    if grobid_files:
        with open(CONFIG_PATH_GROBID, 'r') as f:
            config = json.load(f)
        url = f"http://{config['grobid_server']}:{config['grobid_port']}/api/version"
        grobid_version = requests.get(url).text
    else:
        grobid_version = "0"
    return grobid_version

def create_task_process(files, do_grobid, do_softcite):
    _swift = Swift(config_harvester)
    download_files(_swift, PUBLICATIONS_DOWNLOAD_DIR, files)
    start_time = time()
    if do_grobid:
        run_grobid(CONFIG_PATH_GROBID, PUBLICATIONS_DOWNLOAD_DIR, GrobidClient)
    time_grobid = time()
    logger_console.info(f"Runtime for Grobid: {round(time_grobid - start_time, 3)}s for {len(files)} files")
    if do_softcite:
        run_softcite(CONFIG_PATH_SOFTCITE, PUBLICATIONS_DOWNLOAD_DIR, smc)
    time_softcite = time()
    logger_console.info(f"Runtime for Softcite: {round(time_softcite - time_grobid, 3)}s for {len(files)} files")
    logger_console.info(f"Total runtime: {round(time_softcite - start_time, 3)}s for {len(files)} files")
    local_files = glob(PUBLICATIONS_DOWNLOAD_DIR + '*')
    softcite_version = get_softcite_version(local_files)
    grobid_version = get_grobid_version(local_files)
    upload_and_clean_up(_swift, PUBLICATIONS_DOWNLOAD_DIR)
    db_handler: DBHandler = DBHandler(engine=engine, table_name='harvested_status_table', swift_handler=_swift)
    try:
        db_handler.update_database(grobid_version, softcite_version)  # update database
    except Exception as e:
        logger_console.debug(e)

