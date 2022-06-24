from unittest import TestCase
from unittest.mock import MagicMock, patch

from sqlalchemy.engine import Engine

from infrastructure.database.db_handler import DBHandler

TESTED_MODULE = 'infrastructure.database.db_handler'


class UpdateDatabase(TestCase):

    @patch(f'{TESTED_MODULE}.DBHandler._get_lmdb_content_pickle')
    @patch(f'{TESTED_MODULE}.DBHandler._get_lmdb_content_str')
    @patch(f'{TESTED_MODULE}.generateStoragePath')
    @patch(f'{TESTED_MODULE}.OvhPath')
    @patch(f'{TESTED_MODULE}.ProcessedEntry')
    @patch(f'{TESTED_MODULE}.DBHandler.write_entity_batch')
    def test_given_no_local_doi_uuid_when_call_update_database_then_no_calls_of_some_functions(
            self, mock_write_entity_batch, mock_processed_entry, mock_ovh_path,
            mock_generate_storage_path, mock_get_lmdb_content_str,
            mock_get_lmdb_content_pickle
    ):
        # Given
        mock_engine: Engine = MagicMock()
        table: str = 'false_table'
        mock_swift_handler: any = MagicMock()
        mock_swift_handler.config.return_value = {'publications_dump': 'false_pub_dump', 'lmdb_size_Go': 1}

        db_handler: DBHandler = DBHandler(mock_engine, table, mock_swift_handler)

        mock_get_lmdb_content_pickle.return_value = []
        mock_get_lmdb_content_str.return_value = []
        mock_generate_storage_path.return_value = None
        mock_ovh_path.return_value = None
        mock_swift_handler.get_swift_list.return_value = []
        mock_processed_entry.return_value = None
        mock_write_entity_batch.return_value = None

        expected_nb_calls_lmdb_content_pickle: int = 1
        expected_nb_calls_lmdb_content_str: int = 1
        expected_nb_calls_generate_storage_path: int = 0
        expected_nb_calls_ovh_path: int = 0
        expected_nb_calls_get_swift_list: int = 0
        expected_nb_calls_processed_entry: int = 0
        expected_nb_calls_write_entity_batch: int = 0

        # When
        db_handler.update_database()

        # Then
        assert mock_get_lmdb_content_pickle.call_count == expected_nb_calls_lmdb_content_pickle
        assert mock_get_lmdb_content_str.call_count == expected_nb_calls_lmdb_content_str
        assert mock_generate_storage_path.call_count == expected_nb_calls_generate_storage_path
        assert mock_ovh_path.call_count == expected_nb_calls_ovh_path
        assert mock_swift_handler.get_swift_list.call_count == expected_nb_calls_get_swift_list
        assert mock_processed_entry.call_count == expected_nb_calls_processed_entry
        assert mock_write_entity_batch.call_count == expected_nb_calls_write_entity_batch

    @patch(f'{TESTED_MODULE}.DBHandler._get_lmdb_content_pickle')
    @patch(f'{TESTED_MODULE}.DBHandler._get_lmdb_content_str')
    @patch(f'{TESTED_MODULE}.generateStoragePath')
    @patch(f'{TESTED_MODULE}.OvhPath')
    @patch(f'{TESTED_MODULE}.ProcessedEntry')
    @patch(f'{TESTED_MODULE}.DBHandler.write_entity_batch')
    def test_given_3_local_doi_uuid_when_call_update_database_and_all_in_swift_storage_then_calls_of_every_functions_with_expected_nb_calls(
            self, mock_write_entity_batch, mock_processed_entry, mock_ovh_path,
            mock_generate_storage_path, mock_get_lmdb_content_str,
            mock_get_lmdb_content_pickle
    ):
        # Given
        mock_engine: Engine = MagicMock()
        table: str = 'false_table'
        mock_swift_handler: any = MagicMock()
        mock_swift_handler.config.return_value = {'publications_dump': 'false_pub_dump', 'lmdb_size_Go': 1}

        db_handler: DBHandler = DBHandler(mock_engine, table, mock_swift_handler)

        mock_get_lmdb_content_pickle.return_value = {
            'uuid_1': {'harvester_used': 'fake_harvester_used_1', 'domain': 'fake_domain_1',
                       'url_used': 'fake_url_used_1'},
            'uuid_2': {'harvester_used': 'fake_harvester_used_2', 'domain': 'fake_domain_2',
                       'url_used': 'fake_url_used_2'},
            'uuid_3': {'harvester_used': 'fake_harvester_used_3', 'domain': 'fake_domain_3',
                       'url_used': 'fake_url_used_3'}
        }
        mock_get_lmdb_content_str.return_value = [
            (0, 'uuid_1', 5),
            (0, 'uuid_2', 5),
            (0, 'uuid_3', 5),
        ]
        mock_generate_storage_path.return_value = 'fake_path_uuid'
        mock_ovh_path.return_value = 'fake_path_storage_ovh'
        mock_swift_handler.get_swift_list.return_value = ['fake_path_storage_ovh']
        mock_processed_entry.return_value = MagicMock()
        mock_write_entity_batch.return_value = None

        expected_nb_calls_lmdb_content_pickle: int = 1
        expected_nb_calls_lmdb_content_str: int = 1
        expected_nb_calls_generate_storage_path: int = 3
        expected_nb_calls_ovh_path: int = 3
        expected_nb_calls_get_swift_list: int = 3
        expected_nb_calls_processed_entry: int = 3
        expected_nb_calls_write_entity_batch: int = 1

        # When

        db_handler.update_database()

        # Then
        assert mock_get_lmdb_content_pickle.call_count == expected_nb_calls_lmdb_content_pickle
        assert mock_get_lmdb_content_str.call_count == expected_nb_calls_lmdb_content_str
        assert mock_generate_storage_path.call_count == expected_nb_calls_generate_storage_path
        assert mock_ovh_path.call_count == expected_nb_calls_ovh_path
        assert mock_swift_handler.get_swift_list.call_count == expected_nb_calls_get_swift_list
        assert mock_processed_entry.call_count == expected_nb_calls_processed_entry
        assert mock_write_entity_batch.call_count == expected_nb_calls_write_entity_batch

    @patch(f'{TESTED_MODULE}.DBHandler._get_lmdb_content_pickle')
    @patch(f'{TESTED_MODULE}.DBHandler._get_lmdb_content_str')
    @patch(f'{TESTED_MODULE}.generateStoragePath')
    @patch(f'{TESTED_MODULE}.OvhPath')
    @patch(f'{TESTED_MODULE}.ProcessedEntry')
    @patch(f'{TESTED_MODULE}.DBHandler.write_entity_batch')
    def test_given_3_local_doi_uuid_when_call_update_database_and_only_2_in_swift_storage_then_calls_of_every_functions_with_expected_nb_calls(
            self, mock_write_entity_batch, mock_processed_entry, mock_ovh_path,
            mock_generate_storage_path, mock_get_lmdb_content_str,
            mock_get_lmdb_content_pickle
    ):
        # Given
        mock_engine: Engine = MagicMock()
        table: str = 'false_table'
        mock_swift_handler: any = MagicMock()
        mock_swift_handler.config.return_value = {'publications_dump': 'false_pub_dump', 'lmdb_size_Go': 1}

        db_handler: DBHandler = DBHandler(mock_engine, table, mock_swift_handler)

        mock_get_lmdb_content_pickle.return_value = {
            'uuid_1': {'harvester_used': 'fake_harvester_used_1', 'domain': 'fake_domain_1',
                       'url_used': 'fake_url_used_1'},
            'uuid_2': {'harvester_used': 'fake_harvester_used_2', 'domain': 'fake_domain_2',
                       'url_used': 'fake_url_used_2'},
            'uuid_3': {'harvester_used': 'fake_harvester_used_3', 'domain': 'fake_domain_3',
                       'url_used': 'fake_url_used_3'}
        }
        mock_get_lmdb_content_str.return_value = [
            (0, 'uuid_1', 5),
            (0, 'uuid_2', 5),
            (0, 'uuid_3', 5),
        ]
        mock_generate_storage_path.return_value = 'fake_path_uuid'
        mock_ovh_path.return_value = 'fake_path_storage_ovh'
        mock_swift_handler.get_swift_list.side_effect = [['fake_path_storage_ovh'], ['fake_path_storage_ovh'], []]
        mock_processed_entry.return_value = MagicMock()
        mock_write_entity_batch.return_value = None

        expected_nb_calls_lmdb_content_pickle: int = 1
        expected_nb_calls_lmdb_content_str: int = 1
        expected_nb_calls_generate_storage_path: int = 3
        expected_nb_calls_ovh_path: int = 3
        expected_nb_calls_get_swift_list: int = 3
        expected_nb_calls_processed_entry: int = 2
        expected_nb_calls_write_entity_batch: int = 1

        # When

        db_handler.update_database()

        # Then
        assert mock_get_lmdb_content_pickle.call_count == expected_nb_calls_lmdb_content_pickle
        assert mock_get_lmdb_content_str.call_count == expected_nb_calls_lmdb_content_str
        assert mock_generate_storage_path.call_count == expected_nb_calls_generate_storage_path
        assert mock_ovh_path.call_count == expected_nb_calls_ovh_path
        assert mock_swift_handler.get_swift_list.call_count == expected_nb_calls_get_swift_list
        assert mock_processed_entry.call_count == expected_nb_calls_processed_entry
        assert mock_write_entity_batch.call_count == expected_nb_calls_write_entity_batch

    @patch(f'{TESTED_MODULE}.DBHandler._get_lmdb_content_pickle')
    @patch(f'{TESTED_MODULE}.DBHandler._get_lmdb_content_str')
    @patch(f'{TESTED_MODULE}.generateStoragePath')
    @patch(f'{TESTED_MODULE}.OvhPath')
    @patch(f'{TESTED_MODULE}.ProcessedEntry')
    @patch(f'{TESTED_MODULE}.DBHandler.write_entity_batch')
    def test_given_3_local_doi_uuid_when_call_update_database_and_none_in_swift_storage_then_no_calls_of_some_functions_and_calls_of_others_with_expected_nb_calls(
            self, mock_write_entity_batch, mock_processed_entry, mock_ovh_path,
            mock_generate_storage_path, mock_get_lmdb_content_str,
            mock_get_lmdb_content_pickle
    ):
        # Given
        mock_engine: Engine = MagicMock()
        table: str = 'false_table'
        mock_swift_handler: any = MagicMock()
        mock_swift_handler.config.return_value = {'publications_dump': 'false_pub_dump', 'lmdb_size_Go': 1}

        db_handler: DBHandler = DBHandler(mock_engine, table, mock_swift_handler)

        mock_get_lmdb_content_pickle.return_value = {
            'uuid_1': {'harvester_used': 'fake_harvester_used_1', 'domain': 'fake_domain_1',
                       'url_used': 'fake_url_used_1'},
            'uuid_2': {'harvester_used': 'fake_harvester_used_2', 'domain': 'fake_domain_2',
                       'url_used': 'fake_url_used_2'},
            'uuid_3': {'harvester_used': 'fake_harvester_used_3', 'domain': 'fake_domain_3',
                       'url_used': 'fake_url_used_3'}
        }
        mock_get_lmdb_content_str.return_value = [
            (0, 'uuid_1', 5),
            (0, 'uuid_2', 5),
            (0, 'uuid_3', 5),
        ]
        mock_generate_storage_path.return_value = 'fake_path_uuid'
        mock_ovh_path.return_value = 'fake_path_storage_ovh'
        mock_swift_handler.get_swift_list.side_effect = [[], [], []]
        mock_processed_entry.return_value = MagicMock()
        mock_write_entity_batch.return_value = None

        expected_nb_calls_lmdb_content_pickle: int = 1
        expected_nb_calls_lmdb_content_str: int = 1
        expected_nb_calls_generate_storage_path: int = 3
        expected_nb_calls_ovh_path: int = 3
        expected_nb_calls_get_swift_list: int = 3
        expected_nb_calls_processed_entry: int = 0
        expected_nb_calls_write_entity_batch: int = 0

        # When

        db_handler.update_database()

        # Then
        assert mock_get_lmdb_content_pickle.call_count == expected_nb_calls_lmdb_content_pickle
        assert mock_get_lmdb_content_str.call_count == expected_nb_calls_lmdb_content_str
        assert mock_generate_storage_path.call_count == expected_nb_calls_generate_storage_path
        assert mock_ovh_path.call_count == expected_nb_calls_ovh_path
        assert mock_swift_handler.get_swift_list.call_count == expected_nb_calls_get_swift_list
        assert mock_processed_entry.call_count == expected_nb_calls_processed_entry
        assert mock_write_entity_batch.call_count == expected_nb_calls_write_entity_batch
