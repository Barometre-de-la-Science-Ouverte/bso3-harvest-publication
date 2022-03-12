import lmdb
from sqlalchemy.engine import Engine
from typing import List

from domain.processed_entry import ProcessedEntry

from logger import logger


class DBHandler:
    def __init__(self, engine: Engine, table_name: str, swift_handler):
        self.table_name: str = table_name
        self.engine: Engine = engine
        self.swift_handler = swift_handler
        self.config = swift_handler.config

    def write_entity(self, processed_entry: ProcessedEntry):
        pass

    def write_entity_batch(self, records: List):
        cur = self.engine.raw_connection().cursor()
        args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s)", x).decode("utf-8") for x in records)
        with self.engine.connect() as connection:
            print(f"INSERT INTO {self.table_name} VALUES {args_str}")
            connection.execute(f"INSERT INTO {self.table_name} VALUES {args_str}")

    def _get_uuid_from_path(self, path):
        end_path = path.split('/')[-1]
        uuid = end_path.split('.')[-3]
        return uuid

    def _get_lmdb_content(self, lmdb_path, map_size):
        env = lmdb.open(lmdb_path, map_size=map_size)
        content_str = []
        with env.begin().cursor() as cur:
            for k, v in cur:
                content_str.append((k.decode('utf-8'), v.decode('utf-8')))
        return content_str

    def _is_uuid_in_list(self, uuid, list_uuid):
        return uuid in list_uuid

    def update_database(self):
        logger.debug('enter update databse...')
        container = self.config['publications_dump']
        logger.debug(f'container {container}...')
        lmdb_size = self.config['lmdb_size_Go'] * 1024 * 1024 * 1024

        # remote data
        publications_harvested = self.swift_handler.get_swift_list(container, dir_name='publication')
        logger.debug(f'nb publis in container :  {len(publications_harvested)}...')
        # publications_metadata = self.swift_handler.get_swift_list(container, dir_name='metadata')
        results_grobid = self.swift_handler.get_swift_list(container, dir_name='grobid')
        logger.debug(f'nb results grobid :  {len(results_grobid)}...')
        results_softcite = self.swift_handler.get_swift_list(container, dir_name='softcite')
        logger.debug(f'nb results softcite :  {len(results_softcite)}...')

        # get doi and uuid
        files_uuid_remote = [self._get_uuid_from_path(path) for path in publications_harvested]
        local_doi_uuid = self._get_lmdb_content('data/doi', lmdb_size)
        doi_uuid_uploaded = [content for content in local_doi_uuid if content[1] in files_uuid_remote]
        logger.debug(f'nb uuids uploaded :  {len(doi_uuid_uploaded)}...')

        uuids_softcite = [self._get_uuid_from_path(path) for path in results_softcite]
        logger.debug(f'nb uuids softcite :  {len(uuids_softcite)}...')

        uuids_grobid = [self._get_uuid_from_path(path) for path in results_grobid]

        # [(doi:str, uuid:str, is_harvested:bool, is_processed_softcite:bool, is_processed_grobid:bool)]
        records = [ProcessedEntry(*entry, True, self._is_uuid_in_list(entry[1], uuids_softcite), self._is_uuid_in_list(entry[1], uuids_grobid)) for entry in doi_uuid_uploaded]
        logger.debug(f'nb records to write :  {len(records)}...')
        if records:
            logger.debug(f'write records ...')
            self.write_entity_batch(records)
