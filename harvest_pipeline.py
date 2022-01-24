import os
from config.harvester_config import config_harvester
from config.path_config import METADATA_FILE, DESTINATION_DIR_METADATA
from harvester.OAHarvester import OAHarvester
from load_metadata import load_metadata


METADATA_DUMP = config_harvester['metadata_dump']

NB_SAMPLES = config_harvester['nb_samples_to_harvest']
harvester = OAHarvester(config_harvester, thumbnail=False, sample=NB_SAMPLES, sample_seed=411)

if __name__ == '__main__':

    if len(METADATA_DUMP) > 0:
        metadata_local_file = load_metadata(metadata_container=METADATA_DUMP,
                                            metadata_file=METADATA_FILE,
                                            destination_dir=DESTINATION_DIR_METADATA)
    else:
        metadata_local_file = os.path.join(DESTINATION_DIR_METADATA, METADATA_FILE)

    harvester.harvestUnpaywall(metadata_local_file, reprocess=True)
    harvester.diagnostic()
