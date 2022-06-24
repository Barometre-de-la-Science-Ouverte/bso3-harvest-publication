from sqlalchemy.engine import Engine
from sqlalchemy import create_engine
from utils.singleton import Singleton


class DBConnection(metaclass=Singleton):
    def __init__(self, config: dict) -> None:
        DB_USER = config['db_user']
        DB_PASSWORD = config["db_password"]
        DB_HOST = config["db_host"]
        DB_PORT = config["db_port"]
        DB_NAME = config["db_name"]

        try:
            connection_string = (f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
            self.engine: Engine = create_engine(connection_string)
        except Exception as e:
            print(e)
