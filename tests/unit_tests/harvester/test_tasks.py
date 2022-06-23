from unittest import TestCase, mock
from unittest.mock import patch
from application.server.main.tasks import create_task_harvest_partition

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


        # When create_task_harvest_partition is executed

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
