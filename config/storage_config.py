import os
from config.harvester_config import config_harvester
from config.path_config import PROJECT_DIRNAME

METADATA_DUMP = config_harvester['metadata_dump']
PUBLICATIONS_DUMP = config_harvester['publications_dump']

DESTINATION_DIR_METADATA = os.path.join(PROJECT_DIRNAME, 'tmp')

METADATA_FILE = 'bso-publications-20211214.jsonl.gz'

