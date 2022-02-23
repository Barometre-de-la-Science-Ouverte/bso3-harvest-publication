import abc
import gzip
import json
import os
import unittest
import uuid
from subprocess import CalledProcessError
from unittest import TestCase, mock

from tests.unit_tests.fixtures.harvester import *

from harvester.OAHarvester import (Continue, OAHarvester, _apply_selection,
                                   _check_entry, _count_entries, _download,
                                   _sample_selection, compress,
                                   generateStoragePath, url_to_path)


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
            self.assertEqual(len([i for i in mock_selection if current_idx <= i < current_idx + len(batch)]), len(trimmed_down_list))
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
        mock_processBatch.assert_called_with([expected_url], [expected_filename], [expected_entrie], '')

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
        mock_processBatch.assert_called_with(expected_urls, expected_filenames, expected_entries, '')
    
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
    
    def test__parse_entry(self):
        # Given
        entry_filepath = os.path.join(FIXTURES_PATH, 'entry.json')
        with open(entry_filepath, 'rt') as fp:
            entry_in = json.load(fp)
        parsed_entry_filepath = os.path.join(FIXTURES_PATH, 'parsed_entry.json')
        with open(parsed_entry_filepath, 'rt') as fp:
            entry_out = json.load(fp)
        entry_in['id'] = ids_2_publications[0]
        expected_urls = urls_entry
        expected_entry = entry_out
        expected_filename = filename_2_publications[0]
        # When
        urls, entry, filename = harvester_2_publications._parse_entry(entry_in)
        # Then
        self.assertEqual(entry, expected_entry)
        self.assertEqual(urls, expected_urls)
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
        self.assertEqual(entry['id'], expected_id)


class HarvesterManageFiles(TestCase):

    def setUp(self):
        self.entry = local_entry = entries_2_publications[0]
        self.DATA_PATH = os.path.join(FIXTURES_PATH, 'manageFiles')
        self.filepaths = {
            "dest_path": os.path.join(generateStoragePath(local_entry['id']), local_entry['id']),
            "local_filename": os.path.join(self.DATA_PATH, local_entry['id'] + ".pdf"),
            "local_filename_nxml": os.path.join(self.DATA_PATH, local_entry['id'] + ".nxml"),
            "local_filename_json": os.path.join(self.DATA_PATH, local_entry['id'] + ".json"),
            "thumb_file_small": os.path.join(self.DATA_PATH, local_entry['id'] + '-thumb-small.png'),
            "thumb_file_medium": os.path.join(self.DATA_PATH, local_entry['id'] + '-thumb-medium.png'),
            "thumb_file_large": os.path.join(self.DATA_PATH, local_entry['id'] + '-thumb-large.png'),
        }
    
    def test_generate_thumbnails(self):
        # On n'utilise pas thumbnail
        pass

    def test_write_metadata_file(self):
        # Given
        local_filename_json = os.path.join(FIXTURES_PATH, 'metadata.json.test')
        # When
        harvester_2_publications._write_metadata_file(local_filename_json, self.entry)
        # Then
        self.assertTrue(os.path.exists(local_filename_json))
        with open(local_filename_json, 'r') as f:
            actual_file_content = json.load(f)
        self.assertEqual(self.entry, actual_file_content)
        os.remove(local_filename_json)

    def test_compress_files(self):
        # Given
        # When
        with mock.patch('harvester.OAHarvester.os.remove'):
            harvester_2_publications._compress_files(**self.filepaths, local_entry_id=self.entry['id'], compression_suffix='.gz')
        # Then
        for var_name, file in self.filepaths.items():
            if var_name in ['dest_path', 'thumb_file_small', 'thumb_file_medium', 'thumb_file_large']:
                # thumbnail pas testé car self.Thumbnail=False
                continue
            compressed_file = file + '.gz'
            self.assertTrue(os.path.exists(compressed_file))
            os.remove(compressed_file)
    
    def test_upload_files(self):
        # Given
        harvester_2_publications.swift = abc
        harvester_2_publications.swift.upload_files_to_swift = mock.MagicMock()
        # When
        harvester_2_publications._upload_files(**self.filepaths)
        # Then
        harvester_2_publications.swift.upload_files_to_swift.assert_called_with(\
            harvester_2_publications.storage_publications,\
            [
                self.filepaths['local_filename_nxml'],
            ],\
            self.filepaths['dest_path'])

    @mock.patch('harvester.OAHarvester.shutil.copyfile')
    @mock.patch('harvester.OAHarvester.os.makedirs')
    def test_save_files_locally(self, mock_makedirs, mock_copyfile):
        # Given
        local_dest_path = os.path.join(DATA_PATH, self.filepaths['dest_path'])
        compression_suffix = ''
        # When
        harvester_2_publications._save_files_locally(**self.filepaths, local_entry_id=self.entry['id'], compression_suffix=compression_suffix)
        # Then
        mock_makedirs.assert_called_with(local_dest_path, exist_ok=True)
        mock_copyfile.assert_called_with(self.filepaths['local_filename_json'], os.path.join(local_dest_path, self.entry['id'] + ".json" + compression_suffix))

    @mock.patch('harvester.OAHarvester.os.remove')
    def test_clean_up_files(self, mock_remove):
        # Given
        # When
        harvester_2_publications._clean_up_files(**self.filepaths, local_entry_id=self.entry['id'])
        # Then
        mock_remove.assert_called_with(self.filepaths['local_filename_json'])

    @mock.patch('harvester.OAHarvester.OAHarvester._clean_up_files')
    @mock.patch('harvester.OAHarvester.OAHarvester._save_files_locally')
    @mock.patch('harvester.OAHarvester.OAHarvester._upload_files')
    @mock.patch('harvester.OAHarvester.OAHarvester._compress_files')
    @mock.patch('harvester.OAHarvester.OAHarvester._write_metadata_file')
    @mock.patch('harvester.OAHarvester.OAHarvester._generate_thumbnails')
    def test_manageFiles(self, mock_generate_thumbnails, mock_write_metadata_file,
                         mock_compress_files, mock_upload_files, mock_save_files_locally,
                         mock_clean_up_files):
        # Given
        # When
        harvester_2_publications.manageFiles(self.entry) 
        # Then
        if harvester_2_publications.thumbnail:
            mock_generate_thumbnails.assert_called()
        mock_write_metadata_file.assert_called()
        if harvester_2_publications.config["compression"]:
            mock_compress_files.assert_called()
        if harvester_2_publications.swift:
            mock_upload_files.assert_called()
        else:
            mock_save_files_locally.assert_called()
        mock_clean_up_files.assert_called()


class HarvesterCompress(TestCase):

    def test_compress(self):
        # Given
        expected_pdf_file_compressed = pdf_file + '.gz'
        with open(pdf_file, 'rb') as f:
            expected_file_content = f.read()
        # When
        compress(pdf_file)
        # Then
        self.assertTrue(os.path.exists(expected_pdf_file_compressed))
        with gzip.open(expected_pdf_file_compressed, 'rb') as f:
            actual_file_content = f.read()
        self.assertEqual(expected_file_content, actual_file_content)
        os.remove(expected_pdf_file_compressed)


class HarvesterDownload(TestCase):
    @unittest.skip('No config on github')
    def test_wiley_download(self):
        # Given
        urls, local_entry, filename = wiley_parsed_entry
        # When
        result, _ = _download(urls, filename, local_entry)
        # Then
        self.assertEqual(result, "success")
        self.assertTrue(os.path.getsize(filename) > 0)
        os.remove(filename)
    

    def test_arXiv_url_to_path(self):
        # Given
        ext = ".pdf.gz"
        post_07_arXiv_url = "http://arxiv.org/pdf/1501.00001"
        expected_post_07_arXiv_path = "arxiv/1501/1501.00001/1501.00001" + ext
        pre_07_arXiv_url = "https://arxiv.org/pdf/quant-ph/0602109"
        expected_pre_07_arXiv_path = "quant-ph/0602/0602109/0602109" + ext
        # When
        post_07_arXiv_path = url_to_path(post_07_arXiv_url, ext)
        pre_07_arXiv_path = url_to_path(pre_07_arXiv_url, ext)
        # Then
        self.assertEqual(post_07_arXiv_path, expected_post_07_arXiv_path)
        self.assertEqual(pre_07_arXiv_path, expected_pre_07_arXiv_path)


    @unittest.skip('No config on github')
    def test_arXiv_download(self):
        # Given
        urls, local_entry, filename = arXiv_parsed_entry
        # When
        result, _ = _download(urls, filename, local_entry)
        # Then
        self.assertEqual(result, "success")
        self.assertTrue(os.path.getsize(filename) > 0)
        os.remove(filename)

    
    def test_cloudscrapper_download(self):
        pass
        

if __name__ == '__main__':
    unittest.main()
