import json
from OAHarvester import OAHarvester
from config.path_config import HARVESTER_CONFIG_PATH, PMC_PATH
from logger import logger


def harvest_pmc_sample(config, pmc_path, n_sample=10):
    harvester = OAHarvester(config, thumbnail=False, sample=n_sample)
    harvester.harvestPMC(pmc_path)
    harvester.diagnostic()


if __name__ == "__main__":

    # Load harvester config
    config_harvester = json.load(open(HARVESTER_CONFIG_PATH, 'r'))

    # Harvest publications
    logger.info('Start collecting publications...')
    harvest_pmc_sample(config_harvester, PMC_PATH)
