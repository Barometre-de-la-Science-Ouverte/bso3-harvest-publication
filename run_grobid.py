import os
import sys
from glob import glob
from config.path_config import CONFIG_PATH_GROBID, PUBLICATIONS_DOWNLOAD_DIR

def run_grobid(config_path, data_path, GrobidClient):
    client = GrobidClient(config_path=config_path)
    client.process("processFulltextDocument", data_path, output=data_path, consolidate_citations=True, tei_coordinates=True, force=True, verbose=True, n=4)


if __name__ == "__main__":
    from grobid_client.grobid_client import GrobidClient

    run_grobid(CONFIG_PATH_GROBID, PUBLICATIONS_DOWNLOAD_DIR, GrobidClient)

