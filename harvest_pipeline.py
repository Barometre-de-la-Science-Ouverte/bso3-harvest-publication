import load_metadata
from config.harvester_config import config_harvester, NB_SAMPLE_TO_HARVEST
from config.path_config import INPUT_METADATA_PATH
from config.storage_config import METADATA_DUMP, DESTINATION_DIR_METADATA
from harvester.OAHarvester import OAHarvester

if __name__ == '__main__':
    harvester = OAHarvester(config_harvester, thumbnail=False, sample=NB_SAMPLE_TO_HARVEST, sample_seed=1)

    if len(METADATA_DUMP) > 0:
        metadata_file = load_metadata(METADATA_DUMP, DESTINATION_DIR_METADATA)
    else:
        metadata_file = INPUT_METADATA_PATH

    harvester.harvestUnpaywall(metadata_file)
    harvester.diagnostic()
