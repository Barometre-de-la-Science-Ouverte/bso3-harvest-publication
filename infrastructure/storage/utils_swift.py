import gzip
import os
from typing import List
import pandas as pd
import swiftclient
from time import sleep
from logger import logger
from dotenv import load_dotenv
from config.path_config import OVH_AUTH_URL
from io import BytesIO, TextIOWrapper

# load env variables
path_bso3_env = os.getenv('PATH_ENV_FILE_BSO3')
load_dotenv(path_bso3_env)

SWIFT_SIZE = 10000
key = os.getenv('OS_PASSWORD')
project_name = os.getenv('OS_PROJECT_NAME')
project_id = os.getenv('OS_TENANT_ID')
tenant_name = os.getenv('OS_TENANT_NAME')
username = os.getenv('OS_USERNAME')
user = f'{tenant_name}:{username}'
region_name = os.getenv('REGION_NAME')
project_domain_name = os.getenv('PROJECT_DOMAIN_NAME')
user_domain_name = os.getenv('USER_DOMAIN_NAME')

init_cmd = f'swift --os-auth-url {OVH_AUTH_URL} --auth-version 3 \
      --key {key} --user {user} \
      --os-user-domain-name {user_domain_name} \
      --os-project-domain-name {project_domain_name} \
      --os-project-id {project_id} \
      --os-project-name {project_name} \
      --os-region-name {region_name}'

conn = None
buckets = ['bso_dump', 'glutton_oa_harvesting_v2', 'glutton_oa_harvesting_test']


def get_connection() -> swiftclient.Connection:
    global conn
    if conn is None:
        conn = swiftclient.Connection(
            authurl=OVH_AUTH_URL,
            user=user,
            key=key,
            os_options={
                'user_domain_name': 'Default',
                'project_domain_name': 'Default',
                'project_id': project_id,
                'project_name': project_name,
                'region_name': 'GRA'
            },
            auth_version='3'
        )
    return conn


def list_files(container: str, path: str = '') -> List:
    try:
        connection = get_connection()
        obj = connection.get_object(container, path)
        logger.info(f'{container} last modified: {obj[0]["last-modified"]}')
        return obj[1].decode().split('\n')
    except Exception as e:
        print(e)


def delete_object(container: str, folder: str) -> None:
    connection = get_connection()
    cont = connection.get_container(container)
    for n in [e['name'] for e in cont[1] if folder in e['name']]:
        print(n)
        connection.delete_object(container, n)


def download_object(container: str, filename: str, out: str) -> None:
    logger.debug(f'Downloading {filename} from {container} to {out}')
    cmd = init_cmd + f' download {container} {filename} -o {out}'
    os.system(cmd)


def exists_in_storage(container: str, path: str) -> bool:
    try:
        connection = get_connection()
        connection.head_object(container, path)
        return True
    except:
        return False


def get_objects(container: str, path: str) -> list:
    try:
        connection = get_connection()
        df = pd.read_json(BytesIO(connection.get_object(container, path)[1]), compression='gzip')
    except Exception as e:
        print(e)
        df = pd.DataFrame([])
    return df.to_dict('records')
