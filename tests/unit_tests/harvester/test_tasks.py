from unittest import TestCase
from unittest.mock import MagicMock, patch

from application.server.main.tasks import create_task_harvest_partition, create_task_process, filter_publications
from config.path_config import GROBID_SUFFIX, PUBLICATIONS_DOWNLOAD_DIR, SOFTCITE_SUFFIX
from harvester.OAHarvester import OAHarvester, generateStoragePath
from infrastructure.database.db_handler import DBHandler
from infrastructure.storage.swift import Swift

from grobid_client.grobid_client import GrobidClient
from software_mentions_client.client import software_mentions_client as smc


TESTED_MODULE = 'application.server.main.tasks'


class CreateTaskHarvestPartition(TestCase):
    @patch.object(Swift, '__init__')
    @patch.object(DBHandler, '__init__')
    @patch(f'{TESTED_MODULE}.load_metadata')
    @patch(f'{TESTED_MODULE}.get_partition_size')
    @patch(f'{TESTED_MODULE}.os.path.join')
    @patch(f'{TESTED_MODULE}.write_partitioned_metadata_file')
    @patch(f'{TESTED_MODULE}.write_partitioned_filtered_metadata_file')
    @patch.object(OAHarvester, '__init__')
    @patch.object(OAHarvester, 'harvestUnpaywall')
    @patch.object(OAHarvester, 'diagnostic')
    @patch(f'{TESTED_MODULE}.logger_console.debug')
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

        expected_entries_publications_softcite: list = [(row[0], row[1]) for row in fake_rows_db]
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
        expected_entries_publications_grobid: list = [(row[0], row[1]) for row in fake_rows_db]

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

        expected_entries_publications_softcite: list = [(row[0], row[1]) for row in fake_rows_db]
        expected_entries_publications_grobid: list = [(row[0], row[1]) for row in fake_rows_db]

        # When
        result_entries_publications_softcite, result_entries_publications_grobid = filter_publications(fake_db_handler, fake_softcite_version, fake_grobid_version)

        # Then
        assert result_entries_publications_softcite == expected_entries_publications_softcite
        assert result_entries_publications_grobid == expected_entries_publications_grobid

class CreateTaskProcess(TestCase):
    @patch(f'{TESTED_MODULE}.logger_console.debug')
    @patch.object(Swift, '__init__')
    @patch.object(DBHandler, '__init__')
    @patch(f'{TESTED_MODULE}.filter_publications')
    @patch(f'{TESTED_MODULE}.download_files')
    @patch.object(GrobidClient, '__init__')
    @patch(f'{TESTED_MODULE}.run_grobid')
    @patch.object(smc, '__init__')
    @patch(f'{TESTED_MODULE}.run_softcite')
    @patch(f'{TESTED_MODULE}.logger_console.info')
    @patch(f'{TESTED_MODULE}.glob')
    @patch(f'{TESTED_MODULE}.get_softcite_version')
    @patch(f'{TESTED_MODULE}.get_grobid_version')
    @patch(f'{TESTED_MODULE}.upload_and_clean_up')
    @patch(f'{TESTED_MODULE}.DBHandler.update_database_processing')
    @patch(f'{TESTED_MODULE}.logger_console.exception')
    def test_given_3_uuid_from_files_arg_analyzed_with_too_old_versions_for_all_then_should_get_these_6_in_arguments_for_update_database_processing(
        self, mock_logger_exception, mock_update_database_processing, mock_upload_and_clean_up,
        mock_get_grobid_version, mock_get_softcite_version, mock_glob, mock_logger_info, 
        mock_run_softcite, mock_smc, mock_run_grobid, mock_grobid_client, mock_download_files,
        mock_filter_publications, mock_db_handler, mock_swift, mock_logger_debug
    ):
        # Given
        nb_row: int = 3
        fake_doi: str = 'doi_'
        fake_uuid: str = 'a01b067e-d384-4387-8706-27b9b67927f'
        
        fake_entries_publications_softcite: list = []
        fake_entries_publications_grobid: list = []
        fake_files_arg: list = []
        fake_files_glob: list = []

        expected_arg_update_database_processing_grobid: list = []
        expected_arg_update_database_processing_softcite: list = []

        for i in range(nb_row):
            fdoi: str = f"{fake_doi}{i}"
            fuuid: str = f"{fake_uuid}{i}"
            entry: str = (fdoi, fuuid)
            fake_file_path: str = f"{generateStoragePath(fuuid)}"

            fake_entries_publications_softcite.append(entry)
            fake_entries_publications_grobid.append(entry)
            fake_files_arg.append(f"{fake_file_path}.fake_extension")
            fake_files_glob.append(f"{PUBLICATIONS_DOWNLOAD_DIR}{fake_file_path}.{GROBID_SUFFIX}")
            fake_files_glob.append(f"{PUBLICATIONS_DOWNLOAD_DIR}{fake_file_path}.{SOFTCITE_SUFFIX}")
            
            expected_arg_update_database_processing_grobid.append((*entry, 'grobid', '0.19'))
            expected_arg_update_database_processing_softcite.append((*entry, 'softcite', '0.11'))

        expected_arg_update_database_processing: set = set(expected_arg_update_database_processing_softcite + expected_arg_update_database_processing_grobid)

        fake_spec_grobid_version: str = '0.12'
        fake_spec_softcite_version: str = '0.2'

        mock_logger_debug.return_value = None
        mock_swift.return_value = None
        mock_db_handler.return_value = None
        mock_filter_publications.return_value = (fake_entries_publications_softcite, fake_entries_publications_grobid)
        mock_download_files.return_value = None
        mock_grobid_client.return_value = None
        mock_run_grobid.return_value = None
        mock_smc.return_value = None
        mock_run_softcite.return_value = None
        mock_logger_info.return_value = None
        mock_glob.return_value = fake_files_glob
        mock_get_softcite_version.return_value = '0.11'
        mock_get_grobid_version.return_value = '0.19'
        mock_upload_and_clean_up.return_value = None
        mock_update_database_processing.return_value = None
        mock_logger_exception.return_value = None

        # When
        create_task_process(fake_files_arg, fake_spec_grobid_version, fake_spec_softcite_version)

        # Then
        assert set(mock_update_database_processing.call_args.args[0]) == expected_arg_update_database_processing

        mock_logger_debug.assert_called_once()
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        mock_filter_publications.assert_called_once()
        mock_download_files.assert_called_once()
        mock_run_grobid.assert_called_once()
        mock_run_softcite.assert_called_once()
        mock_logger_info.assert_called_once()
        mock_glob.assert_called_once()
        mock_get_softcite_version.assert_called_once()
        mock_get_grobid_version.assert_called_once()
        mock_upload_and_clean_up.assert_called_once()
        mock_update_database_processing.assert_called_once()
        assert mock_logger_exception.call_count == 0

    @patch(f'{TESTED_MODULE}.logger_console.debug')
    @patch.object(Swift, '__init__')
    @patch.object(DBHandler, '__init__')
    @patch(f'{TESTED_MODULE}.filter_publications')
    @patch(f'{TESTED_MODULE}.download_files')
    @patch.object(GrobidClient, '__init__')
    @patch(f'{TESTED_MODULE}.run_grobid')
    @patch.object(smc, '__init__')
    @patch(f'{TESTED_MODULE}.run_softcite')
    @patch(f'{TESTED_MODULE}.logger_console.info')
    @patch(f'{TESTED_MODULE}.glob')
    @patch(f'{TESTED_MODULE}.get_softcite_version')
    @patch(f'{TESTED_MODULE}.get_grobid_version')
    @patch(f'{TESTED_MODULE}.upload_and_clean_up')
    @patch(f'{TESTED_MODULE}.DBHandler.update_database_processing')
    @patch(f'{TESTED_MODULE}.logger_console.exception')
    def test_given_3_uuid_from_files_arg_and_2_analyzed_with_too_old_versions_for_all_then_should_get_these_4_in_arguments_for_update_database_processing(
        self, mock_logger_exception, mock_update_database_processing, mock_upload_and_clean_up,
        mock_get_grobid_version, mock_get_softcite_version, mock_glob, mock_logger_info, 
        mock_run_softcite, mock_smc, mock_run_grobid, mock_grobid_client, mock_download_files,
        mock_filter_publications, mock_db_handler, mock_swift, mock_logger_debug
    ):
        # Given
        nb_row: int = 3
        fake_doi: str = 'doi_'
        fake_uuid: str = 'a01b067e-d384-4387-8706-27b9b67927f'
        
        fake_entries_publications_softcite: list = []
        fake_entries_publications_grobid: list = []
        fake_files_arg: list = []
        fake_files_glob: list = []

        expected_arg_update_database_processing_grobid: list = []
        expected_arg_update_database_processing_softcite: list = []

        for i in range(nb_row):
            fdoi: str = f"{fake_doi}{i}"
            fuuid: str = f"{fake_uuid}{i}"
            entry: str = (fdoi, fuuid)
            fake_file_path: str = f"{generateStoragePath(fuuid)}"

            fake_entries_publications_softcite.append(entry)
            fake_entries_publications_grobid.append(entry)
            fake_files_arg.append(f"{fake_file_path}.fake_extension")
            fake_files_glob.append(f"{PUBLICATIONS_DOWNLOAD_DIR}{fake_file_path}.{GROBID_SUFFIX}")
            fake_files_glob.append(f"{PUBLICATIONS_DOWNLOAD_DIR}{fake_file_path}.{SOFTCITE_SUFFIX}")
            
            expected_arg_update_database_processing_grobid.append((*entry, 'grobid', '0.19'))
            expected_arg_update_database_processing_softcite.append((*entry, 'softcite', '0.11'))

        fake_files_arg = fake_files_arg[1:]
        fake_files_glob = fake_files_glob[2:]
        expected_arg_update_database_processing: set = set(expected_arg_update_database_processing_softcite[1:] + expected_arg_update_database_processing_grobid[1:])

        fake_spec_grobid_version: str = '0.12'
        fake_spec_softcite_version: str = '0.2'

        mock_logger_debug.return_value = None
        mock_swift.return_value = None
        mock_db_handler.return_value = None
        mock_filter_publications.return_value = (fake_entries_publications_softcite, fake_entries_publications_grobid)
        mock_download_files.return_value = None
        mock_grobid_client.return_value = None
        mock_run_grobid.return_value = None
        mock_smc.return_value = None
        mock_run_softcite.return_value = None
        mock_logger_info.return_value = None
        mock_glob.return_value = fake_files_glob
        mock_get_softcite_version.return_value = '0.11'
        mock_get_grobid_version.return_value = '0.19'
        mock_upload_and_clean_up.return_value = None
        mock_update_database_processing.return_value = None
        mock_logger_exception.return_value = None

        # When
        create_task_process(fake_files_arg, fake_spec_grobid_version, fake_spec_softcite_version)

        # Then
        assert set(mock_update_database_processing.call_args.args[0]) == expected_arg_update_database_processing

        mock_logger_debug.assert_called_once()
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        mock_filter_publications.assert_called_once()
        mock_download_files.assert_called_once()
        mock_run_grobid.assert_called_once()
        mock_run_softcite.assert_called_once()
        mock_logger_info.assert_called_once()
        mock_glob.assert_called_once()
        mock_get_softcite_version.assert_called_once()
        mock_get_grobid_version.assert_called_once()
        mock_upload_and_clean_up.assert_called_once()
        mock_update_database_processing.assert_called_once()
        assert mock_logger_exception.call_count == 0


    @patch(f'{TESTED_MODULE}.logger_console.debug')
    @patch.object(Swift, '__init__')
    @patch.object(DBHandler, '__init__')
    @patch(f'{TESTED_MODULE}.filter_publications')
    @patch(f'{TESTED_MODULE}.download_files')
    @patch.object(GrobidClient, '__init__')
    @patch(f'{TESTED_MODULE}.run_grobid')
    @patch.object(smc, '__init__')
    @patch(f'{TESTED_MODULE}.run_softcite')
    @patch(f'{TESTED_MODULE}.logger_console.info')
    @patch(f'{TESTED_MODULE}.glob')
    @patch(f'{TESTED_MODULE}.get_softcite_version')
    @patch(f'{TESTED_MODULE}.get_grobid_version')
    @patch(f'{TESTED_MODULE}.upload_and_clean_up')
    @patch(f'{TESTED_MODULE}.DBHandler.update_database_processing')
    @patch(f'{TESTED_MODULE}.logger_console.exception')
    def test_given_3_uuid_from_files_arg_and_0_analyzed_with_too_old_versions_for_all_then_should_get_empty_list_in_arguments_for_update_database_processing(
        self, mock_logger_exception, mock_update_database_processing, mock_upload_and_clean_up,
        mock_get_grobid_version, mock_get_softcite_version, mock_glob, mock_logger_info, 
        mock_run_softcite, mock_smc, mock_run_grobid, mock_grobid_client, mock_download_files,
        mock_filter_publications, mock_db_handler, mock_swift, mock_logger_debug
    ):
        # Given
        nb_row: int = 3
        fake_doi: str = 'doi_'
        fake_uuid: str = 'a01b067e-d384-4387-8706-27b9b67927f'
        
        fake_entries_publications_softcite: list = []
        fake_entries_publications_grobid: list = []
        fake_files_arg: list = []
        fake_files_glob: list = []

        for i in range(nb_row):
            fdoi: str = f"{fake_doi}{i}"
            fuuid: str = f"{fake_uuid}{i}"
            fake_file_path: str = f"{generateStoragePath(fuuid)}"

            fake_files_arg.append(f"{fake_file_path}.fake_extension")
            fake_files_glob.append(f"{PUBLICATIONS_DOWNLOAD_DIR}{fake_file_path}.{GROBID_SUFFIX}")
            fake_files_glob.append(f"{PUBLICATIONS_DOWNLOAD_DIR}{fake_file_path}.{SOFTCITE_SUFFIX}")
            
        expected_arg_update_database_processing: set = set()

        fake_spec_grobid_version: str = '0.12'
        fake_spec_softcite_version: str = '0.2'

        mock_logger_debug.return_value = None
        mock_swift.return_value = None
        mock_db_handler.return_value = None
        mock_filter_publications.return_value = (fake_entries_publications_softcite, fake_entries_publications_grobid)
        mock_download_files.return_value = None
        mock_grobid_client.return_value = None
        mock_run_grobid.return_value = None
        mock_smc.return_value = None
        mock_run_softcite.return_value = None
        mock_logger_info.return_value = None
        mock_glob.return_value = fake_files_glob
        mock_get_softcite_version.return_value = '0.11'
        mock_get_grobid_version.return_value = '0.19'
        mock_upload_and_clean_up.return_value = None
        mock_update_database_processing.return_value = None
        mock_logger_exception.return_value = None

        # When
        create_task_process(fake_files_arg, fake_spec_grobid_version, fake_spec_softcite_version)

        # Then
        assert set(mock_update_database_processing.call_args.args[0]) == expected_arg_update_database_processing

        mock_logger_debug.assert_called_once()
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        mock_filter_publications.assert_called_once()
        mock_download_files.assert_called_once()
        assert mock_run_grobid.call_count == 0
        assert mock_run_softcite.call_count == 0
        mock_logger_info.assert_called_once()
        mock_glob.assert_called_once()
        mock_get_softcite_version.assert_called_once()
        mock_get_grobid_version.assert_called_once()
        mock_upload_and_clean_up.assert_called_once()
        mock_update_database_processing.assert_called_once()
        assert mock_logger_exception.call_count == 0
