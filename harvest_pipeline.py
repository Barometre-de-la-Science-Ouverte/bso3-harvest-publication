import json

from config.path_config import CONFIG_PATH
from harvester.OAHarvester import OAHarvester

if __name__ == '__main__':
    config_harvester = json.load(open(CONFIG_PATH, 'r'))
    harvester = OAHarvester(config_harvester, thumbnail=False, sample=5, sample_seed=1)

    metadata_file = 'tmp/bso-publications-staging_20211119_sample_5k.jsonl.gz'

    harvester.harvestUnpaywall(metadata_file)
    harvester.diagnostic()
