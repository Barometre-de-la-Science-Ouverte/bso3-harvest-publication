import os

# Paths
PROJECT_DIRNAME = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(PROJECT_DIRNAME, 'config.json')
DATA_PATH = os.path.join(PROJECT_DIRNAME, 'data')
LOG_PATH = os.path.join(PROJECT_DIRNAME, os.path.join('logs', 'logger.log'))

# Urls
OVH_AUTH_URL = 'https://auth.cloud.ovh.net/v3'
CONTAINER_METADATA = 'bso_dump'
