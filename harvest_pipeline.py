import json
import os

from config.path_config import CONFIG_PATH
from harvester.OAHarvester import OAHarvester
from load_metadata import load_metadata

if __name__ == '__main__':
    # archive_path = load_metadata()

    config_harvester = json.load(open(CONFIG_PATH, 'r'))
    harvester = OAHarvester(config_harvester, thumbnail=False, sample=3000, sample_seed=1)

    filenames = [os.path.join('tmp', 'BSO', 'domaines', f) for f in os.listdir('tmp/BSO/domaines')]

    # harvesting
    for file in filenames:
        harvester.harvestUnpaywall(file)
        harvester.diagnostic()
