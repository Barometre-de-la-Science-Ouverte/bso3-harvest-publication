import os

# Project path
PROJECT_DIRNAME = os.path.dirname(os.path.dirname(__file__))

# Config paths
CONFIG_PATH = os.path.join(PROJECT_DIRNAME, 'config.json')
CONFIG_PATH_TEST = os.path.join(PROJECT_DIRNAME, 'tests', 'unit_tests', 'config_test.json')

# Data path
DATA_PATH = os.path.join(PROJECT_DIRNAME, 'data')
PUBLICATIONS_DOWNLOAD_DIR = os.path.join(PROJECT_DIRNAME, 'downloaded_publications/')
CONFIG_PATH_GROBID = os.path.join(PROJECT_DIRNAME, 'config/config_grobid.json')
CONFIG_PATH_SOFTCITE = os.path.join(PROJECT_DIRNAME, 'config/config_softcite.json')
CONFIG_PATH_OVH = os.path.join(PROJECT_DIRNAME, 'config.json')

# Log path
LOG_PATH = os.path.join(PROJECT_DIRNAME, os.path.join('logs', 'logger.log'))

# Metadata paths
DESTINATION_DIR_METADATA = os.path.join(PROJECT_DIRNAME, 'tmp')
METADATA_LOCAL_FILE = 'bso-publications-5k.jsonl.gz'  # 'bso-publications-20220118.jsonl.gz'

# Prefixes in ovh dump
METADATA_PREFIX = 'metadata'
PUBLICATION_PREFIX = 'publication'
SOFTCITE_PREFIX = 'softcite'
GROBID_PREFIX = 'grobid'