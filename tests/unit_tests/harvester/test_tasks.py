from unittest import TestCase
from unittest.mock import MagicMock, patch

from application.server.main.tasks import create_task_harvest_partition, filter_publications
from harvester.OAHarvester import OAHarvester
from infrastructure.database.db_handler import DBHandler
from infrastructure.storage.swift import Swift

TESTED_MODULE = 'application.server.main.tasks'


class CreateTaskHarvestPartition(TestCase):
    @patch.object(Swift, '__init__')
    @patch.object(DBHandler, '__init__')
    @patch('application.server.main.tasks.load_metadata')
    @patch('application.server.main.tasks.get_partition_size')
    @patch('application.server.main.tasks.os.path.join')
    @patch('application.server.main.tasks.write_partitioned_metadata_file')
    @patch('application.server.main.tasks.write_partitioned_filtered_metadata_file')
    @patch.object(OAHarvester, '__init__')
    @patch.object(OAHarvester, 'harvestUnpaywall')
    @patch.object(OAHarvester, 'diagnostic')
    @patch('application.server.main.tasks.logger_console.debug')
    @patch.object(DBHandler, 'count')
    @patch.object(DBHandler, 'update_database')
    @patch.object(OAHarvester, 'reset_lmdb')
    def test_all_called_the_number_of_times_expected_when_executed(
            self, mock_reset_lmdb, mock_db_update_database, mock_db_count,
            mock_log_debug, mock_diagnostic, mock_harvestUnpaywall, mock_oa_init,
            mock_write_partitioned_filtered_metadata_file,
            mock_write_partitioned_metadata_file, mock_join, mock_get_partition_size,
            mock_load_metadata, mock_db_handler_init, mock_swift_init
    ):
        # Given
        mock_swift_init.return_value = None
        mock_db_handler_init.return_value = None
        mock_load_metadata.return_value = ''
        mock_get_partition_size.return_value = 1
        mock_join.return_value = ''
        mock_write_partitioned_metadata_file.return_value = None
        mock_write_partitioned_filtered_metadata_file.return_value = None
        mock_oa_init.return_value = None
        mock_harvestUnpaywall.return_value = None
        mock_diagnostic.return_value = None
        mock_log_debug.return_value = None
        mock_db_count.return_value = 1
        mock_db_update_database.return_value = None
        mock_reset_lmdb.return_value = None

        # When
        create_task_harvest_partition('', '', '', '', '')

        # Then
        mock_swift_init.assert_called_once()
        mock_db_handler_init.assert_called_once()
        mock_load_metadata.assert_called_once()
        mock_get_partition_size.assert_called_once()
        mock_join.assert_called_once()
        mock_write_partitioned_metadata_file.assert_called_once()
        mock_write_partitioned_filtered_metadata_file.assert_called_once()
        mock_oa_init.assert_called_once()
        mock_harvestUnpaywall.assert_called_once()
        mock_diagnostic.assert_called_once()
        assert mock_log_debug.call_count == 2
        assert mock_db_count.call_count == 2
        mock_db_update_database.assert_called_once()
        mock_reset_lmdb.assert_called_once()


class FilterPublications(TestCase):
    def test_with_same_version_in_db_and_inputs_should_return_empty_list(self):
        # Given
        fake_doi: str = 'doi_'
        fake_uuid: str = 'uuid_'
        fake_is_harvested: bool = False
        fake_softcite_version_db: str = '0.50.9'
        fake_grobid_version_db: str = '0.34.8'
        fake_domain: str = 'arxiv'
        fake_url_used: str = 'http://arxiv.org/fake'

        fake_softcite_version: str = '0.50.9'
        fake_grobid_version: str = '0.34.8'

        nb_row: int = 10

        fake_db_handler: DBHandler = MagicMock()
        fake_db_handler.fetch_all.return_value = [
            (f"{fake_doi}{i}", f"{fake_uuid}{i}", fake_is_harvested, fake_softcite_version_db, fake_grobid_version_db, fake_domain, fake_url_used) for i in range(nb_row)
        ]

        expected_entries_publications_softcite: list = []
        expected_entries_publications_grobid: list = []
        
        # When
        result_entries_publications_softcite, result_entries_publications_grobid = filter_publications(fake_db_handler, fake_softcite_version, fake_grobid_version)

        # Then

        assert result_entries_publications_softcite == expected_entries_publications_softcite
        assert result_entries_publications_grobid == expected_entries_publications_grobid


    def test_with_lesser_version_in_db_for_softcite_and_upper_softcite_given_and_same_grobid_for_db_and_given_should_return_empty_list_for_grobid_and_not_empty_for_softcite(self):
        # Given
        fake_doi: str = 'doi_'
        fake_uuid: str = 'uuid_'
        fake_is_harvested: bool = False
        fake_softcite_version_db: str = '0.5.9'
        fake_grobid_version_db: str = '0.34.8'
        fake_domain: str = 'arxiv'
        fake_url_used: str = 'http://arxiv.org/fake'

        nb_row: int = 10

        fake_softcite_version: str = '0.50.1'
        fake_grobid_version: str = '0.34.8'

        fake_rows_db: list = [
            (f"{fake_doi}{i}", f"{fake_uuid}{i}", fake_is_harvested, fake_softcite_version_db, fake_grobid_version_db, fake_domain, fake_url_used) for i in range(nb_row)
        ]

        fake_db_handler: DBHandler = MagicMock()
        fake_db_handler.fetch_all.return_value = fake_rows_db

        expected_entries_publications_softcite: list = [ (row[0], row[1]) for row in fake_rows_db ]
        expected_entries_publications_grobid: list = []
        
        # When
        result_entries_publications_softcite, result_entries_publications_grobid = filter_publications(fake_db_handler, fake_softcite_version, fake_grobid_version)

        # Then
        assert result_entries_publications_softcite == expected_entries_publications_softcite
        assert result_entries_publications_grobid == expected_entries_publications_grobid


    def test_with_lesser_version_in_db_for_grobid_and_upper_grobid_given_and_same_softcite_for_db_and_given_should_return_empty_list_for_softcite_and_not_empty_for_grobid(self):
        # Given
        fake_doi: str = 'doi_'
        fake_uuid: str = 'uuid_'
        fake_is_harvested: bool = False
        fake_softcite_version_db: str = '0.5.9'
        fake_grobid_version_db: str = '0.34.8'
        fake_domain: str = 'arxiv'
        fake_url_used: str = 'http://arxiv.org/fake'

        nb_row: int = 10

        fake_softcite_version: str = '0.5.9'
        fake_grobid_version: str = '0.59.8'

        fake_rows_db: list = [
            (f"{fake_doi}{i}", f"{fake_uuid}{i}", fake_is_harvested, fake_softcite_version_db, fake_grobid_version_db, fake_domain, fake_url_used) for i in range(nb_row)
        ]

        fake_db_handler: DBHandler = MagicMock()
        fake_db_handler.fetch_all.return_value = fake_rows_db

        expected_entries_publications_softcite: list = []
        expected_entries_publications_grobid: list = [ (row[0], row[1]) for row in fake_rows_db ]
        
        # When
        result_entries_publications_softcite, result_entries_publications_grobid = filter_publications(fake_db_handler, fake_softcite_version, fake_grobid_version)

        # Then
        assert result_entries_publications_softcite == expected_entries_publications_softcite
        assert result_entries_publications_grobid == expected_entries_publications_grobid


    def test_with_upper_version_in_db_for_all_and_lesser_version_for_all_given_should_return_empty_list(self):
        # Given
        fake_doi: str = 'doi_'
        fake_uuid: str = 'uuid_'
        fake_is_harvested: bool = False
        fake_softcite_version_db: str = '0.51.9'
        fake_grobid_version_db: str = '0.47.8'
        fake_domain: str = 'arxiv'
        fake_url_used: str = 'http://arxiv.org/fake'

        nb_row: int = 10

        fake_softcite_version: str = '0.5.9'
        fake_grobid_version: str = '0.34.8'

        fake_rows_db: list = [
            (f"{fake_doi}{i}", f"{fake_uuid}{i}", fake_is_harvested, fake_softcite_version_db, fake_grobid_version_db, fake_domain, fake_url_used) for i in range(nb_row)
        ]

        fake_db_handler: DBHandler = MagicMock()
        fake_db_handler.fetch_all.return_value = fake_rows_db

        expected_entries_publications_softcite: list = []
        expected_entries_publications_grobid: list = []
        
        # When
        result_entries_publications_softcite, result_entries_publications_grobid = filter_publications(fake_db_handler, fake_softcite_version, fake_grobid_version)

        # Then
        assert result_entries_publications_softcite == expected_entries_publications_softcite
        assert result_entries_publications_grobid == expected_entries_publications_grobid



    def test_with_lesser_version_in_db_for_all_and_upper_version_for_all_given_should_return_not_empty_lists(self):
        # Given
        fake_doi: str = 'doi_'
        fake_uuid: str = 'uuid_'
        fake_is_harvested: bool = False
        fake_softcite_version_db: str = '0.5.8'
        fake_grobid_version_db: str = '0.34.7'
        fake_domain: str = 'arxiv'
        fake_url_used: str = 'http://arxiv.org/fake'

        nb_row: int = 10

        fake_softcite_version: str = '0.5.9'
        fake_grobid_version: str = '0.34.8'

        fake_rows_db: list = [
            (f"{fake_doi}{i}", f"{fake_uuid}{i}", fake_is_harvested, fake_softcite_version_db, fake_grobid_version_db, fake_domain, fake_url_used) for i in range(nb_row)
        ]

        fake_db_handler: DBHandler = MagicMock()
        fake_db_handler.fetch_all.return_value = fake_rows_db

        expected_entries_publications_softcite: list = [ (row[0], row[1]) for row in fake_rows_db ]
        expected_entries_publications_grobid: list = [ (row[0], row[1]) for row in fake_rows_db ]
        
        # When
        result_entries_publications_softcite, result_entries_publications_grobid = filter_publications(fake_db_handler, fake_softcite_version, fake_grobid_version)

        # Then
        assert result_entries_publications_softcite == expected_entries_publications_softcite
        assert result_entries_publications_grobid == expected_entries_publications_grobid