import os

# Project path
PROJECT_DIRNAME = os.path.dirname(os.path.dirname(__file__))

# Config paths
CONFIG_PATH = os.path.join(PROJECT_DIRNAME, 'config.json')
CONFIG_PATH_TEST = os.path.join(PROJECT_DIRNAME, 'tests', 'unit_tests', 'config_test.json')

# Data path
DATA_PATH = os.path.join(PROJECT_DIRNAME, 'data')

# Log path
LOG_PATH = os.path.join(PROJECT_DIRNAME, os.path.join('logs', 'logger.log'))

# Metadata paths
DESTINATION_DIR_METADATA = os.path.join(PROJECT_DIRNAME, 'tmp')
METADATA_FILE = 'bso-publications-20211214.jsonl.gz'  # 'bso-publications-staging_20211119_sample_5k.jsonl.gz'
