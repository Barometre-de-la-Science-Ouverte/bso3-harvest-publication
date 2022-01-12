import os
from infrastructure.storage.utils_swift import list_files, download_object

def load_metadata(input_container, destination_dir):
    """
    Download latest publications staging file on bso_dump object storage
    Returns the path of the file once downloaded
    """
    
    metadata_files = list_files(input_container)
    latest_publications_staging = sorted([e for e in metadata_files if ('bso-publications-staging' in e and e.endswith('.jsonl.gz'))])[-1]

    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    if not os.path.exists(f'{destination_dir}/{latest_publications_staging}'):
        download_object(input_container, latest_publications_staging, f'{destination_dir}/{latest_publications_staging}')
    return f'{destination_dir}/{latest_publications_staging}'
