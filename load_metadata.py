import os

from config.harvester_config import config_harvester
from infrastructure.storage.swift import Swift


def load_metadata(metadata_container, metadata_file, destination_dir):
    """
    Download latest publications staging file on bso_dump object storage
    Returns the path of the file once downloaded
    """
    swift_handler = Swift(config_harvester)

    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    if not os.path.exists(f'{destination_dir}/{metadata_file}'):
        swift_handler.download_files(metadata_container, metadata_file, destination_dir)
    return f'{destination_dir}/{metadata_file}'
