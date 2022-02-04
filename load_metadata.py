import os

from config.harvester_config import config_harvester
from infrastructure.storage.swift import Swift


def load_metadata(metadata_container, metadata_file, destination_dir, subfolder_name=''):
    """
    Download latest publications staging file on bso_dump object storage
    Returns the path of the file once downloaded
    """
    swift_handler = Swift(config_harvester)
    local_file_destination = os.path.normpath(os.path.join(f'{destination_dir}', f'{metadata_file}'))

    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)

    if len(subfolder_name) > 0:
        destination_dir_structure = os.path.normpath(os.path.join(destination_dir, subfolder_name))
        if not os.path.isdir(destination_dir_structure):
            os.makedirs(destination_dir_structure)
    else:
        destination_dir_structure = os.path.normpath(destination_dir)

    if not os.path.exists(local_file_destination):
        swift_handler.download_files(metadata_container, metadata_file, destination_dir_structure)
    return local_file_destination
