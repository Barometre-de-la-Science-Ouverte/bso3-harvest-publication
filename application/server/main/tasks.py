import os
from time import time

from grobid_client.grobid_client import GrobidClient
from software_mentions_client.client import software_mentions_client as smc

import load_metadata
from application.server.main.logger import get_logger
from config.harvester_config import config_harvester
from config.path_config import (CONFIG_PATH_GROBID, CONFIG_PATH_SOFTCITE, DESTINATION_DIR_METADATA,
                                PUBLICATIONS_DOWNLOAD_DIR)
from harvester.OAHarvester import OAHarvester
from infrastructure.storage.swift import Swift
from load_metadata import load_metadata
from ovh_handler import download_files, upload_and_clean_up
from run_grobid import run_grobid
from run_softcite import run_softcite

METADATA_DUMP = config_harvester['metadata_dump']
logger = get_logger(__name__)


def create_task_unpaywall(args):
    nb_samples = args.get('nb_samples', 1)
    metadata_file = args.get('metadata_file', '')
    metadata_folder = args.get('metadata_folder', '')

    swift_handler = Swift(config_harvester)

    if (metadata_file == '') and (metadata_folder == ''):
        logger.debug(f'One of the two arguments metadata_file of metadata_folder should be provided !')
    # -----------------------------------------------------------------------------------------------------------------#
    elif (metadata_file != '') and (metadata_folder != ''):
        logger.debug(f'Only one of the two arguments metadata_file of metadata_folder should be provided !')
    # -----------------------------------------------------------------------------------------------------------------#
    elif metadata_file != '':
        logger.debug(f'launching task with args {args}')
        if len(METADATA_DUMP) > 0:
            metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                          metadata_file=metadata_file,
                                          destination_dir=DESTINATION_DIR_METADATA)
        else:
            metadata_file = os.path.join(DESTINATION_DIR_METADATA, metadata_file)
        harvester = OAHarvester(config_harvester, thumbnail=False, sample=nb_samples, sample_seed=1)
        harvester.harvestUnpaywall(metadata_file)
    # -----------------------------------------------------------------------------------------------------------------#
    elif metadata_folder != '':
        logger.debug(f'launching task with args {args}')
        destination_dir = os.path.join(DESTINATION_DIR_METADATA, metadata_folder)
        list_local_files = []
        if len(METADATA_DUMP) > 0:
            files = swift_handler.get_swift_list(container=METADATA_DUMP, dir_name=metadata_folder)
            for file in files:
                metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                              metadata_file=file,
                                              destination_dir=destination_dir)
                list_local_files.append(metadata_file)
        else:
            list_local_files = [f for f in os.listdir(destination_dir)]

        for file in list_local_files:
            print('file:')
            print(file)
            end_file_name = os.path.basename(file)
            file_generic_name = end_file_name.split('.')[-1]
            destination_dir_output = os.path.join(metadata_folder, file_generic_name)
            print('destination dir:')
            print(destination_dir)
            harvester = OAHarvester(config_harvester, thumbnail=False, sample=nb_samples, sample_seed=1)
            harvester.harvestUnpaywall(file, destination_dir=destination_dir_output)


def create_task_process(files):
    _swift = Swift(config_harvester)
    download_files(_swift, PUBLICATIONS_DOWNLOAD_DIR, files)
    start_time = time()
    run_grobid(CONFIG_PATH_GROBID, PUBLICATIONS_DOWNLOAD_DIR, GrobidClient)
    time_grobid = time()
    logger.info(f"Runtime for Grobid: {round(time_grobid - start_time, 3)}s for {len(files)} files")
    run_softcite(CONFIG_PATH_SOFTCITE, PUBLICATIONS_DOWNLOAD_DIR, smc)
    time_softcite = time()
    logger.info(f"Runtime for Softcite: {round(time_softcite - time_grobid, 3)}s for {len(files)} files")
    logger.info(f"Total runtime: {round(time_softcite - start_time, 3)}s for {len(files)} files")
    upload_and_clean_up(_swift, PUBLICATIONS_DOWNLOAD_DIR)
