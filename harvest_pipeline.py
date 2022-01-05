import json
import os

from config.path_config import CONFIG_PATH
from load_metadata import load_metadata
from harvester.OAHarvester import OAHarvester
from harvester.unpaywall_preprocess import create_partition


def harvest_partitions(harvester, partitions_dir):
    partition_files = os.listdir(partitions_dir)
    for file in partition_files:
        harvester.harvestUnpaywall(os.path.join(partitions_dir, file))
        break


if __name__ == '__main__':
    # archive_path = load_metadata()
    archive_path = './tmp/bso-publications-staging_20211119_sample_5k.jsonl.gz'

    config_harvester = json.load(open(CONFIG_PATH, 'r'))
    harvester = OAHarvester(config_harvester, thumbnail=False, sample=100, sample_seed=1)

    harvester.harvestUnpaywall(archive_path)
    harvester.diagnostic()
