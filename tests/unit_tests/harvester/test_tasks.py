from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from application.server.main.tasks import (create_task_harvest_partition,
                                           create_task_process,
                                           get_publications_ids_to_process,
                                           get_publications_ids_to_process)
from config.path_config import (GROBID_SUFFIX, PUBLICATIONS_DOWNLOAD_DIR,
                                SOFTCITE_SUFFIX)
from config.processing_service_namespaces import grobid_ns
from grobid_client.grobid_client import GrobidClient
from infrastructure.database.db_handler import DBHandler
from infrastructure.storage.swift import Swift
from software_mentions_client.client import software_mentions_client as smc
from tests.unit_tests.fixtures.tasks import *

from harvester.OAHarvester import OAHarvester, generateStoragePath

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
    def test_with_identical_service_version_in_db_and_spec_should_return_empty_list(self):
        # Given
        expected_entries_publications_grobid: list = []
        # When
        entries_publications = get_publications_ids_to_process(rows_db, grobid_ns.service_name, identical_spec_grobid_version)
        # Then
        assert entries_publications == expected_entries_publications_grobid

    def test_with_lower_spec_version_should_return_empty_list(self):
        # Given
        expected_entries_publications_grobid: list = []
        # When
        entries_publications = get_publications_ids_to_process(rows_db, grobid_ns.service_name, low_spec_grobid_version)
        # Then
        assert entries_publications == expected_entries_publications_grobid

    def test_with_higher_spec_version_should_return_not_empty_list(self):
        # Given
        expected_entries_publications_grobid: list = [(row[0], row[1]) for row in rows_db]
        # When
        entries_publications = get_publications_ids_to_process(rows_db, grobid_ns.service_name, high_spec_grobid_version)
        # Then
        assert entries_publications == expected_entries_publications_grobid


class CreateTaskProcess(TestCase):
    @patch(f'{TESTED_MODULE}.logger_console')
    @patch(f'{TESTED_MODULE}.Swift')
    @patch(f'{TESTED_MODULE}.DBHandler')
    @patch(f'{TESTED_MODULE}.get_publications_ids_to_process')
    @patch(f'{TESTED_MODULE}.download_files')
    @patch(f'{TESTED_MODULE}.run_processing_services')
    @patch(f'{TESTED_MODULE}.upload_and_clean_up')
    @patch(f'{TESTED_MODULE}.compile_records_for_db')
    def test_with_every_publications_needed_to_be_processed(
        self, mock_compile_records_for_db, mock_upload_and_clean_up,
        mock_run_processing_services, mock_download_files,
        mock_get_publications_ids_to_process, mock_db_handler, mock_swift, mock_logger
    ):
        # Given
        mock_db_handler.return_value._get_uuid_from_path = MagicMock(side_effect=[e[1] for e in entries_publications_grobid] + [e[1] for e in entries_publications_softcite])
        mock_db_handler.return_value.fetch_all = MagicMock()
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_get_publications_ids_to_process.side_effect = [entries_publications_grobid, entries_publications_softcite]
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [expected_arg_update_database_processing_grobid, expected_arg_update_database_processing_softcite]

        # When
        create_task_process(publication_files, high_spec_grobid_version, high_spec_softcite_version)

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        mock_db_handler().fetch_all.assert_called_once()
        assert mock_get_publications_ids_to_process.call_count == 2
        assert mock_download_files.call_count == 2
        mock_download_files.assert_called_with(mock_swift(), softcite_ns.dir, publication_files)
        mock_run_processing_services.assert_called_once()
        assert mock_compile_records_for_db.call_count == 2
        mock_compile_records_for_db.assert_called_with(entries_publications_softcite, softcite_ns, mock_db_handler())
        assert mock_upload_and_clean_up.call_count == 2
        assert mock_db_handler().update_database_processing.call_count == 2
        mock_db_handler().update_database_processing.assert_called_with(expected_arg_update_database_processing_softcite)
    
    @patch(f'{TESTED_MODULE}.logger_console')
    @patch(f'{TESTED_MODULE}.Swift')
    @patch(f'{TESTED_MODULE}.DBHandler')
    @patch(f'{TESTED_MODULE}.get_publications_ids_to_process')
    @patch(f'{TESTED_MODULE}.download_files')
    @patch(f'{TESTED_MODULE}.run_processing_services')
    @patch(f'{TESTED_MODULE}.upload_and_clean_up')
    @patch(f'{TESTED_MODULE}.compile_records_for_db')
    def test_with_one_distinct_publication_needed_to_be_processed_by_each_service(
        self, mock_compile_records_for_db, mock_upload_and_clean_up,
        mock_run_processing_services, mock_download_files,
        mock_get_publications_ids_to_process, mock_db_handler, mock_swift, mock_logger
    ):
        # Given
        mock_db_handler.return_value._get_uuid_from_path = MagicMock(side_effect=[e[1] for e in entries_publications_grobid] + [e[1] for e in entries_publications_softcite])
        mock_db_handler.return_value.fetch_all = MagicMock()
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_get_publications_ids_to_process.side_effect = [entries_publications_grobid[:1], entries_publications_softcite[1:2]]
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [expected_arg_update_database_processing_grobid[:1], expected_arg_update_database_processing_softcite[1:2]]

        # When
        create_task_process(publication_files, high_spec_grobid_version, high_spec_softcite_version)

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        mock_db_handler().fetch_all.assert_called_once()
        assert mock_get_publications_ids_to_process.call_count == 2
        assert mock_download_files.call_count == 2
        mock_download_files.assert_called_with(mock_swift(), softcite_ns.dir, publication_files[1:2])
        mock_run_processing_services.assert_called_once()
        assert mock_compile_records_for_db.call_count == 2
        mock_compile_records_for_db.assert_called_with(entries_publications_softcite[1:2], softcite_ns, mock_db_handler())
        assert mock_upload_and_clean_up.call_count == 2
        assert mock_db_handler().update_database_processing.call_count == 2
        mock_db_handler().update_database_processing.assert_called_with(expected_arg_update_database_processing_softcite[1:2])

    @patch(f'{TESTED_MODULE}.logger_console')
    @patch(f'{TESTED_MODULE}.Swift')
    @patch(f'{TESTED_MODULE}.DBHandler')
    @patch(f'{TESTED_MODULE}.get_publications_ids_to_process')
    @patch(f'{TESTED_MODULE}.download_files')
    @patch(f'{TESTED_MODULE}.run_processing_services')
    @patch(f'{TESTED_MODULE}.upload_and_clean_up')
    @patch(f'{TESTED_MODULE}.compile_records_for_db')
    def test_with_one_publication_needed_to_be_processed_by_grobid(
        self, mock_compile_records_for_db, mock_upload_and_clean_up,
        mock_run_processing_services, mock_download_files,
        mock_get_publications_ids_to_process, mock_db_handler, mock_swift, mock_logger
    ):
        # Given
        mock_db_handler.return_value._get_uuid_from_path = MagicMock(side_effect=[e[1] for e in entries_publications_grobid] + [e[1] for e in entries_publications_softcite])
        mock_db_handler.return_value.fetch_all = MagicMock()
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_get_publications_ids_to_process.side_effect = [entries_publications_grobid[:1], []]
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [expected_arg_update_database_processing_grobid[:1], []]

        # When
        create_task_process(publication_files, high_spec_grobid_version, high_spec_softcite_version)

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        mock_db_handler().fetch_all.assert_called_once()
        assert mock_get_publications_ids_to_process.call_count == 2
        assert mock_download_files.call_count == 1
        mock_download_files.assert_called_with(mock_swift(), grobid_ns.dir, publication_files[:1])
        mock_run_processing_services.assert_called_once()
        assert mock_compile_records_for_db.call_count == 2
        mock_compile_records_for_db.assert_called_with([], softcite_ns, mock_db_handler())
        assert mock_upload_and_clean_up.call_count == 2
        assert mock_db_handler().update_database_processing.call_count == 2
        mock_db_handler().update_database_processing.assert_called_with([])

    @patch(f'{TESTED_MODULE}.logger_console')
    @patch(f'{TESTED_MODULE}.Swift')
    @patch(f'{TESTED_MODULE}.DBHandler')
    @patch(f'{TESTED_MODULE}.get_publications_ids_to_process')
    @patch(f'{TESTED_MODULE}.download_files')
    @patch(f'{TESTED_MODULE}.run_processing_services')
    @patch(f'{TESTED_MODULE}.upload_and_clean_up')
    @patch(f'{TESTED_MODULE}.compile_records_for_db')
    def test_with_one_publication_needed_to_be_processed_by_softcite(
        self, mock_compile_records_for_db, mock_upload_and_clean_up,
        mock_run_processing_services, mock_download_files,
        mock_get_publications_ids_to_process, mock_db_handler, mock_swift, mock_logger
    ):
        # Given
        mock_db_handler.return_value._get_uuid_from_path = MagicMock(side_effect=[e[1] for e in entries_publications_grobid] + [e[1] for e in entries_publications_softcite])
        mock_db_handler.return_value.fetch_all = MagicMock()
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_get_publications_ids_to_process.side_effect = [[], entries_publications_softcite[1:2]]
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [[], expected_arg_update_database_processing_softcite[1:2]]

        # When
        create_task_process(publication_files, high_spec_grobid_version, high_spec_softcite_version)

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        mock_db_handler().fetch_all.assert_called_once()
        assert mock_get_publications_ids_to_process.call_count == 2
        assert mock_download_files.call_count == 1
        mock_download_files.assert_called_with(mock_swift(), softcite_ns.dir, publication_files[1:2])
        mock_run_processing_services.assert_called_once()
        assert mock_compile_records_for_db.call_count == 2
        mock_compile_records_for_db.assert_called_with(entries_publications_softcite[1:2], softcite_ns, mock_db_handler())
        assert mock_upload_and_clean_up.call_count == 2
        assert mock_db_handler().update_database_processing.call_count == 2
        mock_db_handler().update_database_processing.assert_called_with(expected_arg_update_database_processing_softcite[1:2])

    @patch(f'{TESTED_MODULE}.logger_console')
    @patch(f'{TESTED_MODULE}.Swift')
    @patch(f'{TESTED_MODULE}.DBHandler')
    @patch(f'{TESTED_MODULE}.get_publications_ids_to_process')
    @patch(f'{TESTED_MODULE}.download_files')
    @patch(f'{TESTED_MODULE}.run_processing_services')
    @patch(f'{TESTED_MODULE}.upload_and_clean_up')
    @patch(f'{TESTED_MODULE}.compile_records_for_db')
    def test_with_one_publication_needed_to_be_processed(
        self, mock_compile_records_for_db, mock_upload_and_clean_up,
        mock_run_processing_services, mock_download_files,
        mock_get_publications_ids_to_process, mock_db_handler, mock_swift, mock_logger
    ):
        # Given
        mock_db_handler.return_value._get_uuid_from_path = MagicMock(side_effect=[e[1] for e in entries_publications_grobid] + [e[1] for e in entries_publications_softcite])
        mock_db_handler.return_value.fetch_all = MagicMock()
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_get_publications_ids_to_process.side_effect = [entries_publications_grobid[:1], entries_publications_softcite[:1]]
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [expected_arg_update_database_processing_grobid, expected_arg_update_database_processing_softcite]

        # When
        create_task_process(publication_files, high_spec_grobid_version, high_spec_softcite_version)

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        mock_db_handler().fetch_all.assert_called_once()
        assert mock_get_publications_ids_to_process.call_count == 2
        assert mock_download_files.call_count == 2
        mock_download_files.assert_called_with(mock_swift(), softcite_ns.dir, publication_files[:1])
        mock_run_processing_services.assert_called_once()
        assert mock_compile_records_for_db.call_count == 2
        mock_compile_records_for_db.assert_called_with(entries_publications_softcite[:1], softcite_ns, mock_db_handler())
        assert mock_upload_and_clean_up.call_count == 2
        assert mock_db_handler().update_database_processing.call_count == 2
        mock_db_handler().update_database_processing.assert_called_with(expected_arg_update_database_processing_softcite)



    @patch(f'{TESTED_MODULE}.logger_console')
    @patch(f'{TESTED_MODULE}.Swift')
    @patch(f'{TESTED_MODULE}.DBHandler')
    @patch(f'{TESTED_MODULE}.get_publications_ids_to_process')
    @patch(f'{TESTED_MODULE}.download_files')
    @patch(f'{TESTED_MODULE}.run_processing_services')
    @patch(f'{TESTED_MODULE}.upload_and_clean_up')
    @patch(f'{TESTED_MODULE}.compile_records_for_db')
    def test_with_no_publication_needed_to_be_processed(
        self, mock_compile_records_for_db, mock_upload_and_clean_up,
        mock_run_processing_services, mock_download_files,
        mock_get_publications_ids_to_process, mock_db_handler, mock_swift, mock_logger
    ):
        # Given
        mock_get_publications_ids_to_process.return_value = []
        mock_db_handler.return_value._get_uuid_from_path = MagicMock(side_effect=[e[1] for e in entries_publications_grobid] + [e[1] for e in entries_publications_softcite])
        mock_db_handler.return_value.fetch_all = MagicMock()
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [expected_arg_update_database_processing_grobid, expected_arg_update_database_processing_softcite]

        # When
        create_task_process(publication_files, high_spec_grobid_version, high_spec_softcite_version)

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        mock_db_handler().fetch_all.assert_called_once()
        assert mock_get_publications_ids_to_process.call_count == 2
        assert mock_download_files.call_count == 0
        mock_run_processing_services.assert_called_once()
        assert mock_compile_records_for_db.call_count == 2
        mock_compile_records_for_db.assert_called_with([], softcite_ns, mock_db_handler())
        assert mock_upload_and_clean_up.call_count == 2
        assert mock_db_handler().update_database_processing.call_count == 2
        mock_db_handler().update_database_processing.assert_called_with(expected_arg_update_database_processing_softcite)

