import lmdb
from sqlalchemy.engine import Engine
from typing import List

from domain.processed_entry import ProcessedEntry


class DBHandler:
    def __init__(self, engine: Engine, table_name: str, swift_handler):
        self.table_name: str = table_name
        self.engine: Engine = engine
        self.swift_handler = swift_handler
        self.config = swift_handler.config

    def write_entity(self, processed_entry: ProcessedEntry):
        processed_entry.to_dataframe().to_sql(self.table_name, self.engine, if_exists='append', index=False)

    def write_entity_batch(self, entities: List):
        pass

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
        is_in_list = False
        if uuid in list_uuid:
            is_in_list = True
        return is_in_list

    def update_database(self):
        container = self.config['publications_dump']
        lmdb_size = self.config['lmdb_size_Go'] * 1024 * 1024 * 1024

        publications_harvested = self.swift_handler.get_swift_list(self, container, dir_name='publication')
        # publications_metadata = self.swift_handler.get_swift_list(self, container, dir_name='metadata')
        results_grobid = self.swift_handler.get_swift_list(self, container, dir_name='grobid')
        results_softcite = self.swift_handler.get_swift_list(self, container, dir_name='softcite')
        lmdb_content = self._get_lmdb_content('data/doi', lmdb_size)

        # get doi and uuid
        if len(publications_harvested) > 0:
            uuid_in_dump = [self._get_uuid_from_path(path) for path in publications_harvested]
            lmdb_content_doi_uuid = self._get_lmdb_content('data/doi', lmdb_size)
            doi_uuid_uploaded = [(content[0], content[1]) for content in lmdb_content_doi_uuid if
                                 content[1] in uuid_in_dump]

        # get softcite uuid
        if len(results_softcite) > 0:
            uuids_softcite = [self._get_uuid_from_path(path) for path in results_softcite]

        # get grobid uuid
        if len(results_grobid) > 0:
            uuids_grobid = [self._get_uuid_from_path(path) for path in results_grobid]

        # [(doi, uuid, 1/0, 1/0)]
        if (len(publications_harvested) > 0) and (len(results_softcite) > 0) and (len(results_grobid) > 0):
            if (len(doi_uuid_uploaded) > 0) and (len(uuids_softcite) > 0) and (len(uuids_grobid) > 0):
                rows = [(entry[0], entry[1],
                         self._is_uuid_in_list(entry[1], uuids_softcite),
                         self._is_uuid_in_list(entry[1], uuids_grobid) for entry in doi_uuid_uploaded)]

        ## TODO
        