import pickle
from typing import List

import lmdb
from sqlalchemy import text
from sqlalchemy.engine import Engine

from application.server.main.logger import get_logger
from config.logger_config import LOGGER_LEVEL
from config.path_config import PUBLICATION_PREFIX
from domain.ovh_path import OvhPath
from domain.processed_entry import ProcessedEntry
from harvester.OAHarvester import generateStoragePath

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
        extension_publication: str = '.pdf.gz'

        # get uuid entry content (harvester_used and domain are in it)
        dict_local_uuid_entries = self._get_lmdb_content_pickle('data/entries', lmdb_size)

        # Important : lmdb_reset must be reset
        local_doi_uuid = self._get_lmdb_content_str('data/doi', lmdb_size)
        doi_uuid_uploaded: list = []

        for content_tuple in local_doi_uuid:
            full_path_expected_in_remote: str = str(OvhPath(PUBLICATION_PREFIX, generateStoragePath(content_tuple[1]),
                                                            content_tuple[1] + extension_publication))
            publications_harvested_by_path: list = self.swift_handler.get_swift_list(container,
                                                                                     dir_name=full_path_expected_in_remote)
            if len(publications_harvested_by_path) > 0:
                doi_uuid_uploaded.append(content_tuple)

        records = [ProcessedEntry(*entry,
                                  "1",
                                  "0",
                                  "0",
                                  dict_local_uuid_entries[entry[1]]['harvester_used'],
                                  dict_local_uuid_entries[entry[1]]['domain'],
                                  dict_local_uuid_entries[entry[1]]['url_used']) for entry in doi_uuid_uploaded]

        if records:
            self.write_entity_batch(records)
