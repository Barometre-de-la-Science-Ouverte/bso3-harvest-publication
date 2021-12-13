import os

import psycopg2
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime
from sqlalchemy.engine import Engine

"""
from config.env_config import CONFIG_PATH, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

if os.path.isfile(CONFIG_PATH + '/config_local.json'):
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

tickets_table = Table(
    'tickets', meta,
    Column('sys_id', String, primary_key=True),
    Column('numero', String),
    Column('date_de_creation', DateTime),
    Column('objet', String),
    Column('declarant', String),
    Column('premier_groupe_affectation', String),
    Column('priorite', String),
    Column('origine_incident', String),
    Column('type_incident', String),
    Column('categorie', String),
    Column('sous_categorie', String),
    Column('sous_sous_categorie', String),
    Column('environnement', String),
    Column('prediction_ml', String)
)

prediction_table = Table(
    'predictions', meta,
    Column('sys_id', String, primary_key=True),
    Column('prediction', String)
)

annotations_table = Table(
    'annotations', meta,
    Column('sys_id', String, primary_key=True),
    Column('annotation', String),
    Column('date_de_cloture', DateTime)
)

meta.create_all(engine)
"""
