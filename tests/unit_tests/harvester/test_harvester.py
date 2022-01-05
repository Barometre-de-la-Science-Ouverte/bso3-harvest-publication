import gzip
import json
import unittest
import os
from unittest import TestCase, mock
import uuid

from harvester.OAHarvester import OAHarvester, _count_entries, _sample_selection, _check_entry, Continue, _apply_selection
from tests.unit_tests.fixtures.harvester import harvester_2_publications, harvester_2_publications_sample, entries_2_publications, \
    filename_2_publications, urls_2_publications, ids_2_publications, FIXTURES_PATH


class HarvesterCountEntries(TestCase):

    def test_when_wrong_filepath_raise_FileNotFoundError_exception(self):
        wrong_filepath = 'wrong_filepath'

        with self.assertRaises(FileNotFoundError):
            _count_entries(open, wrong_filepath)

    def test_when_2_publications_then_return_2(self):
        filepath_2_publications = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')

        nb_publications = _count_entries(gzip.open, filepath_2_publications)

        self.assertEqual(nb_publications, 2)


class HarvesterSampleSelection(TestCase):

    def test_when_sample_is_4_then_return_list_of_size_4(self):
        nb_sample = 4
        count = 22
        samples = _sample_selection(nb_sample, count, sample_seed=1)
        self.assertEqual(len(samples), nb_sample)

    def test_when_sample_is_0_then_raise_index_error_exception(self):
        sample = 0
        count = 4
        with self.assertRaises(IndexError):
            samples = _sample_selection(sample, count, sample_seed=1)


class HarvesterApplySelection(TestCase):

    def test_when_given_a_list_returns_elements_corresponding_to_selection(self):
        # Given
        nb_sample = 4
        batches = []
        batch = []
        for i in range(22):
            batch.append([chr(i),chr(i+1),chr(i+2)])
        batches.append(batch)
        batch = []
        for i in range(22, 25):
            batch.append([chr(i),chr(i+1),chr(i+2)])
        batches.append(batch)
        mock_selection = [1, 2, 3, 24]
        # When
        current_idx = 0
        for batch_n, batch in enumerate(batches):
            trimmed_down_list = _apply_selection(batch, mock_selection, current_idx)
            # Then
            self.assertEquals(len([i for i in mock_selection if current_idx <= i < current_idx + len(batch)]), len(trimmed_down_list))
            for e in trimmed_down_list:
                self.assertIn(e, batch)
                self.assertIn(batch.index(e), mock_selection)
            current_idx += len(batch)

class HarvestUnpaywall(TestCase):

    def test_when_wrong_filepath_raise_FileNotFoundError_exception(self):
        wrong_filepath = 'wrong_filepath'

        with self.assertRaises(FileNotFoundError):
            harvester_2_publications.harvestUnpaywall(wrong_filepath)

    @mock.patch('harvester.OAHarvester._sample_selection')
    @mock.patch.object(uuid, 'uuid4')
    @mock.patch.object(OAHarvester, 'processBatch')
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test_when_2_publications_and_sample_is_1_then_processBatch_is_called_with_1_element(self, mock_getUUIDByIdentifier, mock_processBatch, mock_uuid4, mock_sample_selection):
        # Given a file path
        filepath = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')
        expected_url = urls_2_publications[0]
        expected_filename = filename_2_publications[0]
        expected_entrie = entries_2_publications[0]
        mock_uuid4.side_effect = ids_2_publications
        mock_getUUIDByIdentifier.return_value = None
        mock_sample_selection.return_value = [0]
        # When harvestUnpaywall is executed
        harvester_2_publications_sample.harvestUnpaywall(filepath, reprocess=True)

        # Then processBatch is executed on
        mock_processBatch.assert_called_with([expected_url], [expected_filename], [expected_entrie])

    @mock.patch.object(uuid, 'uuid4')
    @mock.patch.object(OAHarvester, 'processBatch')
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test_when_2_publications_then_processBatch_is_called(self, mock_getUUIDByIdentifier, mock_processBatch, mock_uuid4):
        # Given a file path
        filepath = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')
        expected_urls = urls_2_publications
        expected_filenames = filename_2_publications
        expected_entries = entries_2_publications
        mock_uuid4.side_effect = ids_2_publications
        mock_getUUIDByIdentifier.return_value = None

        # When harvestUnpaywall is executed
        harvester_2_publications.harvestUnpaywall(filepath, reprocess=True)

        # Then processBatch is executed on
        mock_processBatch.assert_called_with(expected_urls, expected_filenames, expected_entries)
    
    @mock.patch.object(uuid, "uuid4")
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__get_batch_generator(self, mock_getUUIDByIdentifier, mock_uuid4):
        # Given
        filepath = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')
        count = _count_entries(gzip.open, filepath)
        reprocess = False
        batch_size = 100
        expected_urls = urls_2_publications
        expected_filenames = filename_2_publications
        expected_entries = entries_2_publications
        mock_getUUIDByIdentifier.return_value = None
        mock_uuid4.side_effect = ids_2_publications
        # When
        batch_gen = harvester_2_publications._get_batch_generator(filepath, count, reprocess, batch_size)
        # Then
        for i, batch in enumerate(batch_gen):
            urls = [e[0] for e in batch]
            entries = [e[1] for e in batch]
            filenames = [e[2] for e in batch]
            self.assertEqual(urls, expected_urls[i*batch_size:(i+1)*batch_size])
            self.assertEqual(entries, expected_entries[i*batch_size:(i+1)*batch_size])
            self.assertEqual(filenames, expected_filenames[i*batch_size:(i+1)*batch_size])
    
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__process_entry_when_entry_already_processed(self, mock_getUUIDByIdentifier):
        # Given
        filepath = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')
        with gzip.open(filepath, 'rt') as fp:
            file_content = [json.loads(line) for line in fp]
        entry = file_content[0]
        expected_entries = entries_2_publications
        mock_getUUIDByIdentifier.return_value = 'abc'.encode("UTF-8")
        # Then
        with self.assertRaises(Continue):
            harvester_2_publications._process_entry(entry, reprocess=False)
    
    @mock.patch.object(uuid, 'uuid4')
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__process_entry_when_new_entry(self, mock_getUUIDByIdentifier, mock_uuid4):
        # Given
        filepath = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')
        with gzip.open(filepath, 'rt') as fp:
            file_content = [json.loads(line) for line in fp]
        entry_in = file_content[0]
        expected_url = urls_2_publications[0]
        expected_entry = entries_2_publications[0]
        expected_filename = filename_2_publications[0]
        mock_getUUIDByIdentifier.return_value = None
        mock_uuid4.return_value = ids_2_publications[0]
        # When
        url, entry, filename = harvester_2_publications._process_entry(entry_in, reprocess=False)
        # Then
        self.assertIsNotNone(entry['id'])
        self.assertEqual(entry, expected_entry)
        self.assertEqual(url, expected_url)
        self.assertEqual(filename, expected_filename)
    
    def test__parse_entry_when_new_entry(self):
        # Given
        filepath = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')
        with gzip.open(filepath, 'rt') as fp:
            file_content = [json.loads(line) for line in fp]
        entry_in = file_content[0]
        expected_url = urls_2_publications[0]
        expected_entry = entries_2_publications[0]
        expected_filename = filename_2_publications[0]
        entry_in['id'] = ids_2_publications[0]
        # When
        url, entry, filename = harvester_2_publications._parse_entry(entry_in)
        # Then
        self.assertEqual(entry, expected_entry)
        self.assertEqual(url, expected_url)
        self.assertEqual(filename, expected_filename)
    
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__check_entry_when_entry_already_processed(self, mock_getUUIDByIdentifier):
        # Given
        filepath = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')
        with gzip.open(filepath, 'rt') as fp:
            file_content = [json.loads(line) for line in fp]
        entry = file_content[0]
        expected_entries = entries_2_publications
        mock_getUUIDByIdentifier.return_value = 'abc'.encode("UTF-8")
        # Then
        with self.assertRaises(Continue):
            _check_entry(entry, entry['doi'], harvester_2_publications.getUUIDByIdentifier, reprocess=False, env=harvester_2_publications.env, env_doi=harvester_2_publications.env_doi)
        # self.assertIsNotNone(entry['id'])
    
    @mock.patch.object(uuid, "uuid4")
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__check_entry_when_new_entry(self, mock_getUUIDByIdentifier, mock_uuid4):
        # Given
        filepath = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')
        with gzip.open(filepath, 'rt') as fp:
            file_content = [json.loads(line) for line in fp]
        entry = file_content[0]
        expected_id = ids_2_publications[0]
        mock_getUUIDByIdentifier.return_value = None
        mock_uuid4.return_value = expected_id
        # When
        _check_entry(entry, entry['doi'], harvester_2_publications.getUUIDByIdentifier, reprocess=False, env=harvester_2_publications.env, env_doi=harvester_2_publications.env_doi)
        # Then
        self.assertEquals(entry['id'], expected_id)


if __name__ == '__main__':
    unittest.main()
