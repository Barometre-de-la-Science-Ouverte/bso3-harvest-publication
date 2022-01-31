import os
import load_metadata
from config.harvester_config import config_harvester
from config.path_config import DESTINATION_DIR_METADATA
from harvester.OAHarvester import OAHarvester
from load_metadata import load_metadata
from application.server.main.logger import get_logger

METADATA_DUMP = config_harvester['metadata_dump']
logger = get_logger(__name__)

def create_task_unpaywall(args):
    nb_samples = args.get('nb_samples', 1)
    metadata_file = args.get('metadata_file')
    logger.debug(f'launching task with args {args}')

    if len(METADATA_DUMP) > 0:
        metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                      metadata_file=metadata_file,
                                      destination_dir=DESTINATION_DIR_METADATA)
    else:
        metadata_file = os.path.join(DESTINATION_DIR_METADATA, metadata_file)

    harvester = OAHarvester(config_harvester, thumbnail=False, sample=nb_samples, sample_seed=1)
    harvester.harvestUnpaywall(metadata_file)
