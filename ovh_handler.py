import argparse
import json
import os
from typing import List
from swift import Swift
from glob import glob
from config.path_config import CONFIG_PATH_OVH, PUBLICATIONS_DOWNLOAD_DIR


def generateStoragePath(identifier):
    """Convert a file name into a path with file prefix as directory paths:
    123456789 -> 12/34/56/78/"""
    return os.path.join(identifier[:2], identifier[2:4], identifier[4:6], identifier[6:8])


def get_partitions(_swift:Swift, partition_size:int) -> List:
    """Return a list a partitions of gzipped or flat pdf files"""
    files = _swift.get_swift_list()
    files = [file for file in files if (file.endswith('.pdf.gz') or file.endswith('.pdf'))]
    partitions = [files[i:i+partition_size] for i in range(0, len(files), partition_size)]
    return partitions


def download_files(_swift, dest_dir, files):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    return _swift.download_files(files, dest_dir)


def upload_and_clean_up(_swift, local_dir):
    files = glob(local_dir + '*')
    upload_files = [(file, os.path.join('processed', generateStoragePath(os.path.basename(file)), os.path.basename(file)))
        for file in files if not (file.endswith('.pdf') or file.endswith('.pdf.gz'))]
    _swift.upload_files_to_swift(upload_files)
    for file in files:
        os.remove(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()
    upload = args.upload
    download = args.download
    
    config_harvester = json.load(open(CONFIG_PATH_OVH,'r'))
    _swift = Swift(config_harvester)
    if download:
        download_files(_swift, PUBLICATIONS_DOWNLOAD_DIR)
    if upload:
        upload_and_clean_up(_swift, PUBLICATIONS_DOWNLOAD_DIR)