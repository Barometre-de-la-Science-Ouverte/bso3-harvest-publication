import os

# Paths
PROJECT_DIRNAME = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(PROJECT_DIRNAME, 'config.json')
CONFIG_PATH_TEST = os.path.join(PROJECT_DIRNAME, 'tests', 'unit_tests', 'config_test.json')
DATA_PATH = os.path.join(PROJECT_DIRNAME, 'data')
LOG_PATH = os.path.join(PROJECT_DIRNAME, os.path.join('logs', 'logger.log'))
LOCAL_METADATA_PATH = 'tmp/bso-publications-staging_20211119_sample_5k.jsonl.gz'

