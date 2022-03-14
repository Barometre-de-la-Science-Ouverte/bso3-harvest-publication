import psycopg2
from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.engine import Engine

from config.harvester_config import config_harvester

# postgre config
IS_DB_LOCAL = str(config_harvester['is_db_local'])
DB_USER = config_harvester['db']['db_user']
DB_PASSWORD = config_harvester['db']['db_password']
DB_HOST = config_harvester['db']['db_host']
DB_PORT = config_harvester['db']['db_port']
DB_NAME = config_harvester['db']['db_name']

if IS_DB_LOCAL == '1':
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
    Column('uuid', String),
    Column('is_harvested', String),
    Column('is_processed_softcite', String),
    Column('is_processed_grobid', String),
    Column('harvester_used', String),
    Column('domain', String)
)

meta.create_all(engine)
