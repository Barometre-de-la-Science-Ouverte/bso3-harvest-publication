import os

PROJECT_DIRNAME = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(PROJECT_DIRNAME, 'config.json')
PMC_PATH = os.path.join(os.path.dirname(PROJECT_DIRNAME), 'oa_file_list.txt')
DATA_PATH= os.path.join(PROJECT_DIRNAME, 'data')

LOG_PATH = os.path.join(PROJECT_DIRNAME, 'harvester.log')

OVH_AUTH_URL = 'https://auth.cloud.ovh.net/v3'

"""
DB_USER =
DB_PASSWORD =
DB_HOST = 
DB_PORT = 
DB_NAME

import json
import os

CONFIGURATION_LOCAL_PATH = os.path.dirname(__file__)
CONFIGURATION_PATH_ENV = '/opt/services/conf/config.json'



LOG_PATH = config_env['log_file_path']

"""
