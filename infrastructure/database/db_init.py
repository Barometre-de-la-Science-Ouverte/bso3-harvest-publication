import psycopg2
from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.engine import Engine

from static_config.config_generator import config_json
DB_USER = config_json["db"]["DB_USER"]
DB_HOST = config_json["db"]["DB_HOST"]
DB_PORT = config_json["db"]["DB_PORT"]
DB_NAME = config_json["db"]["DB_NAME"]
DB_PASSWORD = config_json["db"]["DB_PASSWORD"]

try:
    connection = psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_NAME)
    connection_string = (f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
except Exception as e:
    print(f"Using testing.postgres, because : {e}")
    from testing.postgresql import Postgresql

    db: Postgresql = Postgresql()
    connection_string: str = db.url()

engine: Engine = create_engine(connection_string)
meta = MetaData()

harvested_status_table = Table(
    "harvested_status_table",
    meta,
    Column("doi", String, primary_key=True),
    Column("uuid", String),
    Column("is_harvested", String),
    Column("softcite_version", String),
    Column("grobid_version", String),
    Column("harvester_used", String),
    Column("domain", String),
    Column("url_used", String),
    extend_existing=True,
)

meta.create_all(engine)
