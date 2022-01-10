import json
import os

import psycopg2
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, Boolean
from sqlalchemy.engine import Engine

from config.path_config import CONFIG_PATH, PROJECT_DIRNAME

with open(PROJECT_DIRNAME + '/config.json') as f:
    config_env = json.load(f)

IS_DB_LOCAL = str(config_env['is_db_local'])
DB_USER = config_env['db_user']
DB_PASSWORD = config_env['db_password']
DB_HOST = config_env['db_host']
DB_PORT = config_env['db_port']
DB_NAME = config_env['db_name']

if IS_DB_LOCAL == "1":
    from testing.postgresql import Postgresql

    db: Postgresql = Postgresql()
    connection_string: str = db.url()
else:
    connection = psycopg2.connect(user=DB_USER,
                                  password=DB_PASSWORD,
                                  host=DB_HOST,
                                  port=DB_PORT,
                                  database=DB_NAME)

    connection_string = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

engine: Engine = create_engine(connection_string)
meta = MetaData()

harvested_status_table = Table(
    'harvested_status_table', meta,
    Column('doi', String, primary_key=True),
    Column('is_harvested', Boolean),
    Column('harvested_date', DateTime),
    Column('uuid', String)
)

meta.create_all(engine)


