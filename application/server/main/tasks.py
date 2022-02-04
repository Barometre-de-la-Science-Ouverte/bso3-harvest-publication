import os
from time import time

import load_metadata
from application.server.main.logger import get_logger
from grobid_client.grobid_client import GrobidClient
from harvester.OAHarvester import OAHarvester
from infrastructure.storage.swift import Swift
from load_metadata import load_metadata
from ovh_handler import download_files, upload_and_clean_up
from run_grobid import run_grobid
from run_softcite import run_softcite
from software_mentions_client.client import software_mentions_client as smc

from config.harvester_config import config_harvester
from config.path_config import (CONFIG_PATH_GROBID, CONFIG_PATH_OVH,
                                CONFIG_PATH_SOFTCITE, DESTINATION_DIR_METADATA,
                                PUBLICATIONS_DOWNLOAD_DIR)

METADATA_DUMP = config_harvester['metadata_dump']
logger = get_logger(__name__)

def create_task_unpaywall(args):
    nb_samples = args.get('nb_samples', 1)
    metadata_file = args.get('metadata_file')
    logger.debug(f'launching task with args {args}')

    if len(METADATA_DUMP) > 0:
        metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                      metadata_file=metadata_file,
                                      destination_dir=DESTINATION_DIR_METADATA)
    else:
        metadata_file = os.path.join(DESTINATION_DIR_METADATA, metadata_file)

    harvester = OAHarvester(config_harvester, thumbnail=False, sample=nb_samples, sample_seed=1)
    harvester.harvestUnpaywall(metadata_file)


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
