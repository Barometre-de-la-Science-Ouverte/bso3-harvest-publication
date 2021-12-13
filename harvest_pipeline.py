import json
import os

from config.path_config import HARVESTER_CONFIG_PATH
from load_metadata import load_metadata
from harvester.OAHarvester import OAHarvester
from harvester.unpaywall_preprocess import create_partition


def harvest_partitions(harvester, partitions_dir):
    partition_files = os.listdir(partitions_dir)
    for file in partition_files:
        harvester.harvestUnpaywall(os.path.join(partitions_dir, file))
        break

if __name__ == '__main__':
    archive_path = load_metadata()
    partitions_dir = f'{os.path.dirname(archive_path)}/partitions/'
    create_partition(archive_path, output=partitions_dir, nb_bins=10)

    config_harvester = json.load(open(HARVESTER_CONFIG_PATH, 'r'))
    harvester = OAHarvester(config_harvester, thumbnail=False, sample=10)

    harvest_partitions(harvester, partitions_dir)
    harvester.diagnostic()
