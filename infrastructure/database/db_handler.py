import pickle

import lmdb
from sqlalchemy.engine import Engine
from sqlalchemy import text
from typing import List

from config.path_config import PUBLICATION_PREFIX, GROBID_PREFIX, SOFTCITE_PREFIX, DEFAULT_GROBID_TAG, \
    DEFAULT_SOFTCITE_TAG
from domain.processed_entry import ProcessedEntry
from application.server.main.logger import get_logger
from config.logger_config import LOGGER_LEVEL
logger = get_logger(__name__, level=LOGGER_LEVEL)



class DBHandler:
    def __init__(self, engine: Engine, table_name: str, swift_handler):
        self.table_name: str = table_name
        self.engine: Engine = engine
        self.swift_handler = swift_handler
        self.config = swift_handler.config

    def fetch_all(self):
        """Return the table content"""
        result = self.engine.execute(f'SELECT * FROM {self.table_name}')
        return [ProcessedEntry(*entry) for entry in result.fetchall()]

    def count(self):
        """Return the number of rows in the table"""
        # (X,) rows
        return self.engine.execute(f'SELECT count(*) FROM {self.table_name}').fetchone()[0]

    def write_entity_batch(self, records: List):
        cur = self.engine.raw_connection().cursor()
        args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", x).decode("utf-8") for x in records)
        with self.engine.connect() as connection:
            try:
                statement = f"""
                    INSERT INTO {self.table_name} (doi, uuid, is_harvested, softcite_version, grobid_version, harvester_used, domain, url_used)
                    VALUES {args_str}
                    ON CONFLICT (uuid) DO UPDATE
                        SET softcite_version = excluded.softcite_version,
                            grobid_version = excluded.grobid_version;
                """
                connection.execute(text(statement))
            except Exception:
                logger.error('Writing to postgres error : ', exc_info=True)

    def _get_uuid_from_path(self, path):
        end_path = path.split('/')[-1]
        uuid = end_path.split('.')[-3]
        return uuid

    def _get_lmdb_content_str(self, lmdb_path, map_size):
        env = lmdb.open(lmdb_path, map_size=map_size)
        content_str = []
        with env.begin().cursor() as cur:
            for doi, uuid in cur:
                content_str.append((doi.decode('utf-8'), uuid.decode('utf-8')))
        return content_str

    def _get_lmdb_content_pickle(self, lmdb_path, map_size):
        env = lmdb.open(lmdb_path, map_size=map_size)
        dict_content = {}
        with env.begin().cursor() as cur:
            for k, v in cur:
                dict_content[k.decode('utf-8')] = pickle.loads(v)
        return dict_content

    def _is_uuid_in_list(self, uuid, list_uuid):
        if uuid in list_uuid:
            return "1"
        else:
            return "0"

    def _get_harvester_used(self, uuid):
        pass

    def update_database_processing(self, entries, grobid_version, softcite_version):
        DUMMY_DATA = ""
        records = [ProcessedEntry(*entry,
                                  "1",
                                  grobid_version if grobid_version else "0",
                                  softcite_version if softcite_version else "0",
                                  DUMMY_DATA,
                                  DUMMY_DATA,
                                  DUMMY_DATA) for entry in entries]

        if records:
            self.write_entity_batch(records)

    def update_database(self):
        container = self.config['publications_dump']
        lmdb_size = self.config['lmdb_size_Go'] * 1024 * 1024 * 1024

        # get uuid entry content (harvester_used and domain are in it)
        dict_local_uuid_entries = self._get_lmdb_content_pickle('data/entries', lmdb_size)

        publications_harvested = self.swift_handler.get_swift_list(container, dir_name=PUBLICATION_PREFIX)
        files_uuid_remote = [self._get_uuid_from_path(path) for path in publications_harvested]
        local_doi_uuid = self._get_lmdb_content_str('data/doi', lmdb_size)
        doi_uuid_uploaded = [content_tuple for content_tuple in local_doi_uuid if
                             content_tuple[1] in files_uuid_remote]  #

        # results_softcite = self.swift_handler.get_swift_list(container, dir_name=SOFTCITE_PREFIX)
        # uuids_softcite = [self._get_uuid_from_path(path) for path in results_softcite]

        # results_grobid = self.swift_handler.get_swift_list(container, dir_name=GROBID_PREFIX)
        # uuids_grobid = [self._get_uuid_from_path(path) for path in results_grobid]

        # [(doi:str, uuid:str, is_harvested:bool, is_processed_softcite:bool, is_processed_grobid:bool),
        # harvester_used:str, domain:str, url_used:str]
        records = [ProcessedEntry(*entry,
                                  "1",
                                  "0",
                                  "0",
                                  dict_local_uuid_entries[entry[1]]['harvester_used'],
                                  dict_local_uuid_entries[entry[1]]['domain'],
                                  dict_local_uuid_entries[entry[1]]['url_used']) for entry in doi_uuid_uploaded]

        if records:
            self.write_entity_batch(records)
