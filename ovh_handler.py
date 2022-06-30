import os
from glob import glob
from types import SimpleNamespace
from typing import List

from config.db_config import engine
from config.harvester_config import config_harvester
from config.path_config import (PUBLICATION_PREFIX, GROBID_PREFIX,
                                GROBID_SUFFIX, SOFTCITE_PREFIX,
                                SOFTCITE_SUFFIX)
from domain.ovh_path import OvhPath
from infrastructure.database.db_handler import DBHandler
from infrastructure.storage.swift import Swift
import shutil
from application.server.main.logger import get_logger
from config.logger_config import LOGGER_LEVEL
logger_console = get_logger(__name__, level=LOGGER_LEVEL)

def generateStoragePath(identifier):
    """Convert a file name into a path with file prefix as directory paths:
    123456789 -> 12/34/56/78/123456789/"""
    return OvhPath(identifier[:2], identifier[2:4], identifier[4:6], identifier[6:8], identifier)


def get_partitions(_swift: Swift, partition_size: int) -> List:
    """Return a list of partitions of gzipped pdf files"""
    db_handler: DBHandler = DBHandler(engine=engine, table_name="harvested_status_table", swift_handler=_swift)
    files = sorted([
            str(OvhPath(PUBLICATION_PREFIX, generateStoragePath(record[1]), record[1] + ".pdf.gz"))
            for record in db_handler.fetch_all()
        ])
    partitions = [files[i : i + partition_size] for i in range(0, len(files), partition_size)]
    return partitions


def download_files(_swift, dest_dir, files):
    """Make dest_dir if it does not exist and download files not already present in dest_dir"""
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    files = [file for file in files if not os.path.exists(os.path.join(dest_dir, file))]
    try:
        _swift.download_files(_swift.config["publications_dump"], files, dest_dir)
    except shutil.Error:
        logger_console.exception(exc_info=True)



def upload_and_clean_up(_swift: Swift, service_ns: SimpleNamespace):
    files = glob(service_ns.dir + "*")
    files_to_upload = [
        (file, OvhPath(service_ns.prefix, generateStoragePath(os.path.basename(file).split(".")[0]), os.path.basename(file)))
        for file in files if file.endswith(service_ns.suffix)
    ]
    _swift.upload_files_to_swift(_swift.config["publications_dump"], files_to_upload)
    for file in files:
        os.remove(file)
