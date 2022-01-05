import os
from infrastructure.storage.utils_swift import (list_files, download_object)
from config.path_config import CONTAINER_METADATA


def load_metadata() -> str:
    """Download latest publications staging file on bso_dump object storage
    Returns the path of the file once downloaded"""
    container = CONTAINER_METADATA
    bso_dump_files = list_files(container)
    latest_publications_staging = sorted([e for e in bso_dump_files if ('bso-publications-staging' in e and e.endswith('.jsonl.gz'))])[-1]
    dest_path = './tmp'
    if not os.path.isdir(dest_path):
        os.makedirs(dest_path)
    if not os.path.exists(f'{dest_path}/{latest_publications_staging}'):
        # logging.info(f"Downloading {latest_publications_staging} to {dest_path}/{latest_publications_staging}")
        download_object(container, latest_publications_staging, f'{dest_path}/{latest_publications_staging}')
    return f'{dest_path}/{latest_publications_staging}'
