import os

# Paths
PROJECT_DIRNAME = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(PROJECT_DIRNAME, 'config.json')
PMC_PATH = os.path.join(os.path.dirname(PROJECT_DIRNAME), 'oa_file_list.txt')
DATA_PATH = os.path.join(PROJECT_DIRNAME, 'data')
LOG_PATH = os.path.join(PROJECT_DIRNAME, os.path.join('logs', 'logger.log'))

# Urls
OVH_AUTH_URL = 'https://auth.cloud.ovh.net/v3'
