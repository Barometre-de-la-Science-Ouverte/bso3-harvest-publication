import json
import os

from config.path_config import CONFIG_PATH
from harvester.OAHarvester import OAHarvester
from load_metadata import load_metadata

if __name__ == '__main__':
    # archive_path = load_metadata()

    config_harvester = json.load(open(CONFIG_PATH, 'r'))
    harvester = OAHarvester(config_harvester, thumbnail=False, sample=5, sample_seed=1)

    metadata_file = 'tmp/bso-publications-staging_20211119_sample_5k.jsonl.gz'

    harvester.harvestUnpaywall(metadata_file)
    harvester.diagnostic()
