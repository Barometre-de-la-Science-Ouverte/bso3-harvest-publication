import os
from config.harvester_config import config_harvester
from config.path_config import METADATA_LOCAL_FILE, DESTINATION_DIR_METADATA
from harvester.OAHarvester import OAHarvester
from infrastructure.database.db_handler import DBHandler
from config.db_config import engine
from load_metadata import load_metadata
from infrastructure.storage.swift import Swift


METADATA_DUMP = config_harvester['metadata_dump']

NB_SAMPLES = 10
harvester = OAHarvester(config_harvester, sample=NB_SAMPLES, sample_seed=413)
swift_handler = Swift(config_harvester)
db_handler: DBHandler = DBHandler(engine=engine, table_name='harvested_status_table', swift_handler=swift_handler)

if __name__ == '__main__':

    if len(METADATA_DUMP) > 0:
        metadata_local_file = load_metadata(metadata_container=METADATA_DUMP,
                                            metadata_file=METADATA_LOCAL_FILE,
                                            destination_dir=DESTINATION_DIR_METADATA)
    else:
        metadata_local_file = os.path.join(DESTINATION_DIR_METADATA, METADATA_LOCAL_FILE)

    harvester.harvestUnpaywall(metadata_local_file)
    harvester.diagnostic()
    db_handler.update_database()
