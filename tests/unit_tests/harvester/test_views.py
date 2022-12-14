from typing import Callable
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock

from config.processing_service_namespaces import grobid_ns, softcite_ns, datastet_ns
from application.server.main.views import filter_publications, get_files_to_process, prepare_process_task_arguments
from tests.unit_tests.fixtures.views import *


TESTED_MODULE = "application.server.main.views"

grobid_filter = lambda record: record.grobid_version < grobid_ns.spec_version


class FilterPublications(TestCase):
    def tearDown(self):
        del grobid_ns.spec_version

    def test_with_identical_service_version_in_db_and_spec_should_return_empty_list(self):
        # Given
        grobid_ns.spec_version = identical_spec_grobid_version
        expected_entries_publications_grobid: list = []
        # When
        entries_publications = filter_publications(rows_db, grobid_filter)
        # Then
        self.assertEqual(entries_publications, expected_entries_publications_grobid)

    def test_with_lower_spec_version_should_return_empty_list(self):
        # Given
        expected_entries_publications_grobid: list = []
        grobid_ns.spec_version = low_spec_grobid_version
        # When
        entries_publications = filter_publications(rows_db, grobid_filter)
        # Then
        self.assertEqual(entries_publications, expected_entries_publications_grobid)

    def test_with_higher_spec_version_should_return_not_empty_list(self):
        # Given
        expected_entries_publications_grobid: list = rows_db
        grobid_ns.spec_version = high_spec_grobid_version
        # When
        entries_publications = filter_publications(rows_db, grobid_filter)
        # Then
        self.assertEqual(entries_publications, expected_entries_publications_grobid)


class GetFilesToProcess(TestCase):
    def tearDown(self):
        del grobid_ns.spec_version

    @patch(f"{TESTED_MODULE}.filter_publications")
    def test_get_files_to_process(self, mock_filter_publications):
        # Given
        mock_filter_publications.return_value = entries_to_process
        grobid_ns.spec_version = high_spec_grobid_version
        # When
        files_to_process = get_files_to_process(rows_db, grobid_filter)
        # Then
        self.assertEqual(files_to_process, expected_files_to_process)


class PrepareProcessTaskArguments(TestCase):
    def tearDown(self):
        del grobid_ns.spec_version
        del grobid_ns.partitions
        del softcite_ns.spec_version
        del softcite_ns.partitions
        del datastet_ns.spec_version
        del datastet_ns.partitions

    @patch(f"{TESTED_MODULE}.DBHandler")
    @patch(f"{TESTED_MODULE}.Swift")
    def test_prepare_process_task_arguments(self, mock_swift, mock_DBHandler):
        # Given
        mock_db_handler = Mock() 
        mock_db_handler.fetch_all = Mock(return_value=rows_db)
        mock_DBHandler.return_value = mock_db_handler
        
        grobid_ns.spec_version = low_spec_grobid_version
        softcite_ns.spec_version = high_spec_softcite_version
        datastet_ns.spec_version = low_spec_datastet_version
        partition_size = 2
        # When
        prepare_process_task_arguments(partition_size, grobid_ns, softcite_ns, datastet_ns)
        # Then
        self.assertEqual(grobid_ns.partitions, [[], [], [], [], []])
        self.assertEqual(softcite_ns.partitions, expected_partitions)
        self.assertEqual(datastet_ns.partitions, [[], [], [], [], []])