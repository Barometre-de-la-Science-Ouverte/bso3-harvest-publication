import pickle

import lmdb
from sqlalchemy.engine import Engine
from typing import List

from config.path_config import PUBLICATION_PREFIX, GROBID_PREFIX, SOFTCITE_PREFIX
from domain.processed_entry import ProcessedEntry
from logger import logger


class DBHandler:
    def __init__(self, engine: Engine, table_name: str, swift_handler):
        self.table_name: str = table_name
        self.engine: Engine = engine
        self.swift_handler = swift_handler
        self.config = swift_handler.config

    def write_entity_batch(self, records: List, grobid_version, softcite_version):
        logger.debug(f'Entering write entity...')
        cur = self.engine.raw_connection().cursor()
        args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s)", x).decode("utf-8") for x in records)
        logger.debug(f'str to write : {args_str}')
        with self.engine.connect() as connection:
            try:
                connection.execute(f"INSERT INTO {self.table_name} " \
                                   f"VALUES {args_str} " \
                                   f"ON DUPLICATE KEY UPDATE " \
                                   f"softcite_version = {softcite_version}, " \
                                   f"grobid_version = {grobid_version} ")
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

    def update_database(self, grobid_version=None, softcite_version=None):
        logger.debug(f'Entering update database...')
        if not grobid_version:
            grobid_version = "0.7.1-SNAPSHOT"
        if not softcite_version:
            softcite_version = "0.7.1-SNAPSHOT"

        container = self.config['publications_dump']
        lmdb_size = self.config['lmdb_size_Go'] * 1024 * 1024 * 1024

        # get uuid entry content (harvester_used and domain are in it)
        dict_local_uuid_entries = self._get_lmdb_content_pickle('data/entries', lmdb_size)

        publications_harvested = self.swift_handler.get_swift_list(container, dir_name=PUBLICATION_PREFIX)
        logger.debug(f'Example of publi : {publications_harvested[0]}')
        files_uuid_remote = [self._get_uuid_from_path(path) for path in publications_harvested]
        if len(files_uuid_remote) > 0:
            logger.debug(f'Example of uuid remote : {files_uuid_remote[0]}')
        else:
            logger.debug(f'Uuid remote empty: {files_uuid_remote}')
        local_doi_uuid = self._get_lmdb_content_str('data/doi', lmdb_size)
        logger.debug(f'Example of local doi_uuid idx 0: {local_doi_uuid[0]}')
        logger.debug(f'Example of local doi_uuid idx 0 uuid: {local_doi_uuid[0][1]}')
        doi_uuid_uploaded = [content for content in local_doi_uuid if content[1] in files_uuid_remote]  #
        logger.debug(f'Len files uuid remote : {len(files_uuid_remote)}')

        if len(local_doi_uuid) > 0:
            logger.debug(f'Example of local_doi_uuid : {local_doi_uuid[0]}')
        else:
            logger.debug(f'Empty local_doi_uuid : {local_doi_uuid}')

        if len(doi_uuid_uploaded) > 0:
            logger.debug(f'Example of doi_uuid_uploaded : {doi_uuid_uploaded[0]}')
        else:
            logger.debug(f'Empty doi_uuid_uploaded : {doi_uuid_uploaded}')

        logger.debug(f'Length doi_uuid_uploaded: {len(doi_uuid_uploaded)}')

        results_softcite = self.swift_handler.get_swift_list(container, dir_name=SOFTCITE_PREFIX)
        uuids_softcite = [self._get_uuid_from_path(path) for path in results_softcite]

        results_grobid = self.swift_handler.get_swift_list(container, dir_name=GROBID_PREFIX)
        uuids_grobid = [self._get_uuid_from_path(path) for path in results_grobid]

        # [(doi:str, uuid:str, is_harvested:bool, is_processed_softcite:bool, is_processed_grobid:bool),
        # harvester_used:str, domain:str]
        records = [ProcessedEntry(*entry,
                                  "1",
                                  "0",  # self._is_uuid_in_list(entry[1], uuids_softcite)
                                  "0",  # self._is_uuid_in_list(entry[1], uuids_grobid)
                                  dict_local_uuid_entries[entry[1]]['harvester_used'],
                                  dict_local_uuid_entries[entry[1]]['domain']) for entry in doi_uuid_uploaded]
        logger.debug(f'Records to write: {records}')

        if records:
            logger.debug('There are records to write...')
            self.write_entity_batch(records, softcite_version, grobid_version)
