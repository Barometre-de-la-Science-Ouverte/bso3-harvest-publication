import os

PROJECT_DIRNAME = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(PROJECT_DIRNAME, 'config.json')
PMC_PATH = os.path.join(os.path.dirname(PROJECT_DIRNAME), 'oa_file_list.txt')

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

if os.path.isfile(CONFIGURATION_LOCAL_PATH + '/config_local.json'):
    with open(CONFIGURATION_LOCAL_PATH + '/config_local.json') as f:
        config_env = json.load(f)
else:
    with open(CONFIGURATION_PATH_ENV) as f:
        config_env = json.load(f)

SERVICE_NOW_LOGIN = config_env['login_service_now']
SERVICE_NOW_PWD = config_env['password_service_now']

DB_USER = config_env['db_user']
DB_PASSWORD = config_env['db_password']
DB_HOST = config_env['db_host']
DB_PORT = config_env['db_port']
DB_NAME = config_env['db_name']

LOG_PATH = config_env['log_file_path']

"""
