import os

from config.harvester_config import config_harvester
from infrastructure.storage.swift import Swift


def load_metadata(input_container, destination_dir):
    """
    Download latest publications staging file on bso_dump object storage
    Returns the path of the file once downloaded
    """
    swift_handler = Swift(config_harvester)
    latest_publications_staging = 'bso-publication-20211214.jsonl.gz'

    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    if not os.path.exists(f'{destination_dir}/{latest_publications_staging}'):
        swift_handler.download_file(input_container,
                                    latest_publications_staging,
                                    destination_dir)
    return f'{destination_dir}/{latest_publications_staging}'
