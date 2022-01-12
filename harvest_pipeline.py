from config.harvester_config import config_harvester, NB_SAMPLE_TO_HARVEST
from config.path_config import LOCAL_METADATA_PATH
from config.storage_config import METADATA_DUMP, METADATA_FILE, DESTINATION_DIR_METADATA
from harvester.OAHarvester import OAHarvester
from load_metadata import load_metadata

if __name__ == '__main__':
    harvester = OAHarvester(config_harvester, thumbnail=False, sample=NB_SAMPLE_TO_HARVEST, sample_seed=1)

    if len(METADATA_DUMP) > 0:
        metadata_local_file = load_metadata(metadata_container=METADATA_DUMP,
                                            metadata_file=METADATA_FILE,
                                            destination_dir=DESTINATION_DIR_METADATA)
    else:
        metadata_local_file = LOCAL_METADATA_PATH

    harvester.harvestUnpaywall(metadata_local_file)
