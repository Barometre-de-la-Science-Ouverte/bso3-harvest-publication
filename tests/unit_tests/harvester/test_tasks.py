import gzip
import json
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock

from application.server.main.tasks import (
    create_task_harvest_partition,
    create_task_process,
    write_partitioned_filtered_metadata_file,
)
from config.processing_service_namespaces import grobid_ns
from infrastructure.database.db_handler import DBHandler
from infrastructure.storage.swift import Swift
from tests.unit_tests.fixtures.tasks import *

from harvester.OAHarvester import OAHarvester

TESTED_MODULE = "application.server.main.tasks"


class WritePartitionedFilteredMetadataFile(TestCase):
    @patch.object(DBHandler, "__init__")
    def setUp(self, mock_db_handler_init):
        mock_db_handler_init.return_value = None
        self.mock_db_handler = DBHandler()
        self.mock_db_handler.fetch_all = Mock()
        self.mock_db_handler.fetch_all.return_value = []

    def tearDown(self):
        try:
            os.remove(filtered_metadata_filename)
        except:
            print(f"Cannot remove {filtered_metadata_filename}")

    def test_write_partitioned_filtered_metadata_file_with_doi_list(self):
        # Given
        # When
        write_partitioned_filtered_metadata_file(
            self.mock_db_handler,
            source_metadata_file,
            filtered_metadata_filename,
            doi_list,
        )
        # Then
        with gzip.open(filtered_metadata_filename, "rt") as f_in:
            content = f_in.readlines()
        for line in content:
            self.assertIsNotNone(json.loads(line).get('doi'))
        assert content == expected_doi_filtered_content

    def test_write_partitioned_filtered_metadata_file_without_doi_list(self):
        # Given
        with gzip.open(source_metadata_file, "rt") as f_in:
            expected_doi_filtered_content = [
                line for line in f_in.readlines() if json.loads(line).get('doi')
            ]
            expected_doi_filtered_content[-1] = expected_doi_filtered_content[-1].rstrip('\n')
        # When
        write_partitioned_filtered_metadata_file(
            self.mock_db_handler,
            source_metadata_file,
            filtered_metadata_filename,
            [],
        )
        # Then
        with gzip.open(filtered_metadata_filename, "rt") as f_in:
            content = f_in.readlines()
        for line in content:
            self.assertIsNotNone(json.loads(line).get('doi'))
        self.assertEqual(content, expected_doi_filtered_content)


class CreateTaskHarvestPartition(TestCase):
    @patch.object(Swift, "__init__")
    @patch.object(DBHandler, "__init__")
    @patch(f"{TESTED_MODULE}.load_metadata")
    @patch(f"{TESTED_MODULE}.get_partition_size")
    @patch(f"{TESTED_MODULE}.os.path.join")
    @patch(f"{TESTED_MODULE}.write_partitioned_metadata_file")
    @patch(f"{TESTED_MODULE}.write_partitioned_filtered_metadata_file")
    @patch.object(OAHarvester, "__init__")
    @patch.object(OAHarvester, "harvestUnpaywall")
    @patch.object(OAHarvester, "diagnostic")
    @patch(f"{TESTED_MODULE}.logger_console.debug")
    @patch.object(DBHandler, "count")
    @patch.object(DBHandler, "update_database")
    @patch.object(OAHarvester, "reset_lmdb")
    def test_all_called_the_number_of_times_expected_when_executed(
        self,
        mock_reset_lmdb,
        mock_db_update_database,
        mock_db_count,
        mock_log_debug,
        mock_diagnostic,
        mock_harvestUnpaywall,
        mock_oa_init,
        mock_write_partitioned_filtered_metadata_file,
        mock_write_partitioned_metadata_file,
        mock_join,
        mock_get_partition_size,
        mock_load_metadata,
        mock_db_handler_init,
        mock_swift_init,
    ):
        # Given
        mock_swift_init.return_value = None
        mock_db_handler_init.return_value = None
        mock_load_metadata.return_value = ""
        mock_get_partition_size.return_value = 1
        mock_join.return_value = ""
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
        create_task_harvest_partition("", "", "", "", "", "")

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


class CreateTaskProcess(TestCase):
    @patch(f"{TESTED_MODULE}.logger_console")
    @patch(f"{TESTED_MODULE}.Swift")
    @patch(f"{TESTED_MODULE}.DBHandler")
    @patch(f"{TESTED_MODULE}.download_files")
    @patch(f"{TESTED_MODULE}.run_processing_services")
    @patch(f"{TESTED_MODULE}.upload_and_clean_up")
    @patch(f"{TESTED_MODULE}.compile_records_for_db")
    def test_with_every_publications_needed_to_be_processed(
        self,
        mock_compile_records_for_db,
        mock_upload_and_clean_up,
        mock_run_processing_services,
        mock_download_files,
        mock_db_handler,
        mock_swift,
        mock_logger,
    ):
        # Given
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [
            expected_arg_update_database_processing_grobid,
            expected_arg_update_database_processing_softcite,
            expected_arg_update_database_processing_datastet,
        ]
        grobid_partition_files = publication_files
        softcite_partition_files = publication_files
        datastet_partition_files = publication_files

        # When
        create_task_process(
            grobid_partition_files,
            softcite_partition_files,
            datastet_partition_files
        )

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        self.assertEqual(mock_download_files.call_count, 3)
        mock_download_files.assert_called_with(mock_swift(), datastet_ns.dir, datastet_partition_files)
        mock_run_processing_services.assert_called_once()
        self.assertEqual(mock_compile_records_for_db.call_count, 3)
        mock_compile_records_for_db.assert_called_with(datastet_ns, mock_db_handler())
        self.assertEqual(mock_upload_and_clean_up.call_count, 3)
        self.assertEqual(mock_db_handler().update_database_processing.call_count, 3)
        mock_db_handler().update_database_processing.assert_called_with(
            expected_arg_update_database_processing_datastet
        )

    @patch(f"{TESTED_MODULE}.logger_console")
    @patch(f"{TESTED_MODULE}.Swift")
    @patch(f"{TESTED_MODULE}.DBHandler")
    @patch(f"{TESTED_MODULE}.download_files")
    @patch(f"{TESTED_MODULE}.run_processing_services")
    @patch(f"{TESTED_MODULE}.upload_and_clean_up")
    @patch(f"{TESTED_MODULE}.compile_records_for_db")
    def test_with_one_distinct_publication_needed_to_be_processed_by_each_service(
        self,
        mock_compile_records_for_db,
        mock_upload_and_clean_up,
        mock_run_processing_services,
        mock_download_files,
        mock_db_handler,
        mock_swift,
        mock_logger,
    ):
        # Given
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [
            expected_arg_update_database_processing_grobid[:1],
            expected_arg_update_database_processing_softcite[1:2],
            expected_arg_update_database_processing_datastet[2:3],
        ]
        grobid_partition_files = publication_files
        softcite_partition_files = publication_files
        datastet_partition_files = publication_files

        # When
        create_task_process(
            grobid_partition_files[:1],
            softcite_partition_files[1:2],
            datastet_partition_files[2:3]
        )

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        self.assertEqual(mock_download_files.call_count, 3)
        mock_download_files.assert_called_with(mock_swift(), datastet_ns.dir, publication_files[2:3])
        mock_run_processing_services.assert_called_once()
        self.assertEqual(mock_compile_records_for_db.call_count, 3)
        mock_compile_records_for_db.assert_called_with(datastet_ns, mock_db_handler())
        self.assertEqual(mock_upload_and_clean_up.call_count, 3)
        self.assertEqual(mock_db_handler().update_database_processing.call_count, 3)
        mock_db_handler().update_database_processing.assert_called_with(
            expected_arg_update_database_processing_datastet[2:3]
        )

    @patch(f"{TESTED_MODULE}.logger_console")
    @patch(f"{TESTED_MODULE}.Swift")
    @patch(f"{TESTED_MODULE}.DBHandler")
    @patch(f"{TESTED_MODULE}.download_files")
    @patch(f"{TESTED_MODULE}.run_processing_services")
    @patch(f"{TESTED_MODULE}.upload_and_clean_up")
    @patch(f"{TESTED_MODULE}.compile_records_for_db")
    def test_with_one_publication_needed_to_be_processed_by_grobid(
        self,
        mock_compile_records_for_db,
        mock_upload_and_clean_up,
        mock_run_processing_services,
        mock_download_files,
        mock_db_handler,
        mock_swift,
        mock_logger,
    ):
        # Given
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [
            expected_arg_update_database_processing_grobid[:1],
            [],
            [],
        ]
        grobid_partition_files = publication_files[:1]
        softcite_partition_files = []
        datastet_partition_files = []

        # When
        create_task_process(
            grobid_partition_files,
            softcite_partition_files,
            datastet_partition_files
        )

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        self.assertEqual(mock_download_files.call_count, 3)
        mock_download_files.assert_called_with(mock_swift(), datastet_ns.dir, datastet_partition_files)
        mock_run_processing_services.assert_called_once()
        self.assertEqual(mock_compile_records_for_db.call_count, 3)
        mock_compile_records_for_db.assert_called_with(datastet_ns, mock_db_handler())
        self.assertEqual(mock_upload_and_clean_up.call_count, 3)
        self.assertEqual(mock_db_handler().update_database_processing.call_count, 3)
        mock_db_handler().update_database_processing.assert_called_with(
            []
        )


    @patch(f"{TESTED_MODULE}.logger_console")
    @patch(f"{TESTED_MODULE}.Swift")
    @patch(f"{TESTED_MODULE}.DBHandler")
    @patch(f"{TESTED_MODULE}.download_files")
    @patch(f"{TESTED_MODULE}.run_processing_services")
    @patch(f"{TESTED_MODULE}.upload_and_clean_up")
    @patch(f"{TESTED_MODULE}.compile_records_for_db")
    def test_with_one_publication_needed_to_be_processed_by_softcite(
        self,
        mock_compile_records_for_db,
        mock_upload_and_clean_up,
        mock_run_processing_services,
        mock_download_files,
        mock_db_handler,
        mock_swift,
        mock_logger,
    ):
        # Given
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [
            [],
            expected_arg_update_database_processing_softcite[1:2],
            [],
        ]
        grobid_partition_files = publication_files[:1]
        softcite_partition_files = []
        datastet_partition_files = []

        # When
        create_task_process(
            grobid_partition_files,
            softcite_partition_files,
            datastet_partition_files
        )

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        self.assertEqual(mock_download_files.call_count, 3)
        mock_download_files.assert_called_with(mock_swift(), datastet_ns.dir, datastet_partition_files)
        mock_run_processing_services.assert_called_once()
        self.assertEqual(mock_compile_records_for_db.call_count, 3)
        mock_compile_records_for_db.assert_called_with(datastet_ns, mock_db_handler())
        self.assertEqual(mock_upload_and_clean_up.call_count, 3)
        self.assertEqual(mock_db_handler().update_database_processing.call_count, 3)
        mock_db_handler().update_database_processing.assert_called_with(
            []
        )

    @patch(f"{TESTED_MODULE}.logger_console")
    @patch(f"{TESTED_MODULE}.Swift")
    @patch(f"{TESTED_MODULE}.DBHandler")
    @patch(f"{TESTED_MODULE}.download_files")
    @patch(f"{TESTED_MODULE}.run_processing_services")
    @patch(f"{TESTED_MODULE}.upload_and_clean_up")
    @patch(f"{TESTED_MODULE}.compile_records_for_db")
    def test_with_one_publication_needed_to_be_processed_by_datastet(
        self,
        mock_compile_records_for_db,
        mock_upload_and_clean_up,
        mock_run_processing_services,
        mock_download_files,
        mock_db_handler,
        mock_swift,
        mock_logger,
    ):
        # Given
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [
            [],
            [],
            expected_arg_update_database_processing_datastet[2:3],
        ]
        grobid_partition_files = publication_files[:1]
        softcite_partition_files = []
        datastet_partition_files = []

        # When
        create_task_process(
            grobid_partition_files,
            softcite_partition_files,
            datastet_partition_files
        )

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        self.assertEqual(mock_download_files.call_count, 3)
        mock_download_files.assert_called_with(mock_swift(), datastet_ns.dir, datastet_partition_files)
        mock_run_processing_services.assert_called_once()
        self.assertEqual(mock_compile_records_for_db.call_count, 3)
        mock_compile_records_for_db.assert_called_with(datastet_ns, mock_db_handler())
        self.assertEqual(mock_upload_and_clean_up.call_count, 3)
        self.assertEqual(mock_db_handler().update_database_processing.call_count, 3)
        mock_db_handler().update_database_processing.assert_called_with(
            expected_arg_update_database_processing_datastet[2:3]
        )

    @patch(f"{TESTED_MODULE}.logger_console")
    @patch(f"{TESTED_MODULE}.Swift")
    @patch(f"{TESTED_MODULE}.DBHandler")
    @patch(f"{TESTED_MODULE}.download_files")
    @patch(f"{TESTED_MODULE}.run_processing_services")
    @patch(f"{TESTED_MODULE}.upload_and_clean_up")
    @patch(f"{TESTED_MODULE}.compile_records_for_db")
    def test_with_one_publication_needed_to_be_processed(
        self,
        mock_compile_records_for_db,
        mock_upload_and_clean_up,
        mock_run_processing_services,
        mock_download_files,
        mock_db_handler,
        mock_swift,
        mock_logger,
    ):
        # Given
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [
            expected_arg_update_database_processing_grobid,
            expected_arg_update_database_processing_softcite,
            expected_arg_update_database_processing_datastet,
        ]

        grobid_partition_files = publication_files
        softcite_partition_files = publication_files
        datastet_partition_files = publication_files

        # When
        create_task_process(
            grobid_partition_files,
            softcite_partition_files,
            datastet_partition_files
        )

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        self.assertEqual(mock_download_files.call_count, 3)
        mock_download_files.assert_called_with(mock_swift(), datastet_ns.dir, datastet_partition_files)
        mock_run_processing_services.assert_called_once()
        self.assertEqual(mock_compile_records_for_db.call_count, 3)
        mock_compile_records_for_db.assert_called_with(datastet_ns, mock_db_handler())
        self.assertEqual(mock_upload_and_clean_up.call_count, 3)
        self.assertEqual(mock_db_handler().update_database_processing.call_count, 3)
        mock_db_handler().update_database_processing.assert_called_with(
            expected_arg_update_database_processing_datastet
        )

    @patch(f"{TESTED_MODULE}.logger_console")
    @patch(f"{TESTED_MODULE}.Swift")
    @patch(f"{TESTED_MODULE}.DBHandler")
    @patch(f"{TESTED_MODULE}.download_files")
    @patch(f"{TESTED_MODULE}.run_processing_services")
    @patch(f"{TESTED_MODULE}.upload_and_clean_up")
    @patch(f"{TESTED_MODULE}.compile_records_for_db")
    def test_with_no_publication_needed_to_be_processed(
        self,
        mock_compile_records_for_db,
        mock_upload_and_clean_up,
        mock_run_processing_services,
        mock_download_files,
        mock_db_handler,
        mock_swift,
        mock_logger,
    ):
        # Given
        mock_db_handler.return_value.update_database_processing = MagicMock()
        mock_upload_and_clean_up.return_value = None
        mock_logger.debug = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.exception = MagicMock()
        mock_compile_records_for_db.side_effect = [[], [], []]

        # When
        create_task_process(
            [],
            [],
            [],
        )

        # Then
        mock_swift.assert_called_once()
        mock_db_handler.assert_called_once()
        self.assertEqual(mock_download_files.call_count, 3)
        mock_download_files.assert_called_with(mock_swift(), datastet_ns.dir, [])
        mock_run_processing_services.assert_called_once()
        self.assertEqual(mock_compile_records_for_db.call_count, 3)
        mock_compile_records_for_db.assert_called_with(datastet_ns, mock_db_handler())
        self.assertEqual(mock_upload_and_clean_up.call_count, 3)
        self.assertEqual(mock_db_handler().update_database_processing.call_count, 3)
        mock_db_handler().update_database_processing.assert_called_with(
            []
        )
