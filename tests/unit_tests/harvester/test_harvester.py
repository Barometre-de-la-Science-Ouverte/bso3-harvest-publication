import gzip
import unittest
import os
from unittest import TestCase, mock

from harvester.OAHarvester import OAHarvester, _count_entries, _sample_selection
from tests.unit_tests.fixtures.harvester import harvester_2_publications, entries_2_publications, \
    filename_2_publications, urls_2_publications, FIXTURES_PATH


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
        sample = 22
        count = 4
        samples = _sample_selection(sample, count)
        self.assertEqual(len(samples), sample)

    def test_when_sample_is_0_then_raise_index_error_exception(self):
        sample = 0
        count = 4
        with self.assertRaises(IndexError):
            samples = _sample_selection(sample, count)


class HarvestUnpaywall(TestCase):

    def test_when_wrong_filepath_raise_FileNotFoundError_exception(self):
        wrong_filepath = 'wrong_filepath'

        with self.assertRaises(FileNotFoundError):
            harvester_2_publications.harvestUnpaywall(wrong_filepath)

    @mock.patch.object(OAHarvester, 'processBatch')
    @mock.patch('harvester.OAHarvester._sample_selection')
    def test_when_2_publications_then_processBatch_is_called(self,
                                                             mock_sample_selection,
                                                             mock_processBatch):
        # Given a file path
        filepath = os.path.join(FIXTURES_PATH, 'dump_2_publications.jsonl.gz.test')
        urls = urls_2_publications
        filenames = filename_2_publications
        entries = entries_2_publications

        mock_sample_selection.return_value = [0, 1]

        # When harvestUnpaywall is executed
        harvester_2_publications.harvestUnpaywall(filepath, reprocess=True)

        # Then processBatch is executed on
        mock_processBatch.assert_called_with(urls, filenames, entries)


if __name__ == '__main__':
    unittest.main()
