import abc
import gzip
import unittest
from unittest import TestCase, mock

from harvester.OAHarvester import (Continue, OAHarvester, _apply_selection, _check_entry,
                                   _count_entries, _download_publication, cloudscraper,
                                   _sample_selection, compress, uuid, url_to_path,
                                   generateStoragePath, update_dict, get_nth_key, _process_request,
                                   OvhPath, METADATA_PREFIX, PUBLICATION_PREFIX)
from tests.unit_tests.fixtures.harvester import *


class CountEntries(TestCase):
    def test_when_wrong_filepath_raise_FileNotFoundError_exception(self):
        wrong_filepath = "wrong_filepath"

        with self.assertRaises(FileNotFoundError):
            _count_entries(open, wrong_filepath)

    def test_when_2_publications_then_return_2(self):
        filepath_2_publications = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")

        nb_publications = _count_entries(gzip.open, filepath_2_publications)

        self.assertEqual(nb_publications, 2)


class SampleSelection(TestCase):
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


class ApplySelection(TestCase):
    def test_when_given_a_list_returns_elements_corresponding_to_selection(self):
        # Given
        nb_sample = 4
        batches = []
        batch = []
        for i in range(22):
            batch.append([chr(i), chr(i + 1), chr(i + 2)])
        batches.append(batch)
        batch = []
        for i in range(22, 25):
            batch.append([chr(i), chr(i + 1), chr(i + 2)])
        batches.append(batch)
        mock_selection = [1, 2, 3, 24]
        # When
        current_idx = 0
        for batch_n, batch in enumerate(batches):
            trimmed_down_list = _apply_selection(batch, mock_selection, current_idx)
            # Then
            self.assertEqual(
                len([i for i in mock_selection if current_idx <= i < current_idx + len(batch)]),
                len(trimmed_down_list),
            )
            for e in trimmed_down_list:
                self.assertIn(e, batch)
                self.assertIn(batch.index(e), mock_selection)
            current_idx += len(batch)


class HarvestUnpaywall(TestCase):
    def test_when_wrong_filepath_raise_FileNotFoundError_exception(self):
        wrong_filepath = "wrong_filepath"

        with self.assertRaises(FileNotFoundError):
            harvester_2_publications.harvestUnpaywall(wrong_filepath)

    @mock.patch("harvester.OAHarvester._sample_selection")
    @mock.patch.object(uuid, "uuid4")
    @mock.patch.object(OAHarvester, "processBatch")
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test_when_2_publications_and_sample_is_1_then_processBatch_is_called_with_1_element(
        self, mock_getUUIDByIdentifier, mock_processBatch, mock_uuid4, mock_sample_selection
    ):
        # Given a file path
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        expected_url = sample_urls_lists[0]
        expected_filename = sample_filenames[0]
        expected_entry = sample_entries[0]
        mock_uuid4.side_effect = sample_uuids
        mock_getUUIDByIdentifier.return_value = None
        mock_sample_selection.return_value = [0]

        # When harvestUnpaywall is executed
        harvester_2_publications_sample.harvestUnpaywall(filepath, reprocess=True)

        # Then processBatch is executed on
        mock_processBatch.assert_called_with(
            [expected_url], [expected_filename], [expected_entry], ""
        )

    @mock.patch.object(uuid, "uuid4")
    @mock.patch.object(OAHarvester, "processBatch")
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test_when_2_publications_then_processBatch_is_called(
        self, mock_getUUIDByIdentifier, mock_processBatch, mock_uuid4
    ):
        # Given a file path
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        expected_urls = sample_urls_lists
        expected_filenames = sample_filenames
        expected_entries = sample_entries
        mock_uuid4.side_effect = sample_uuids
        mock_getUUIDByIdentifier.return_value = None

        # When harvestUnpaywall is executed
        harvester_2_publications.harvestUnpaywall(filepath, reprocess=True)

        # Then processBatch is executed on
        mock_processBatch.assert_called_with(
            expected_urls, expected_filenames, expected_entries, ""
        )

    @mock.patch.object(uuid, "uuid4")
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__get_batch_generator(self, mock_getUUIDByIdentifier, mock_uuid4):
        # Given
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        count = _count_entries(gzip.open, filepath)
        reprocess = False
        batch_size = 100
        expected_urls = sample_urls_lists
        expected_filenames = sample_filenames
        expected_entries = sample_entries
        mock_getUUIDByIdentifier.return_value = None
        mock_uuid4.side_effect = sample_uuids
        # When
        batch_gen = harvester_2_publications._get_batch_generator(filepath, count,
                                                                  reprocess, batch_size)
        # Then
        for i, batch in enumerate(batch_gen):
            urls = [e[0] for e in batch]
            entries = [e[1] for e in batch]
            filenames = [e[2] for e in batch]
            self.assertEqual(urls, expected_urls[i * batch_size : (i + 1) * batch_size])
            self.assertEqual(entries, expected_entries[i * batch_size : (i + 1) * batch_size])
            self.assertEqual(filenames, expected_filenames[i * batch_size : (i + 1) * batch_size])

    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__process_entry_when_entry_already_processed(self, mock_getUUIDByIdentifier):
        # Given
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        with gzip.open(filepath, "rt") as fp:
            file_content = [json.loads(line) for line in fp]
        entry = file_content[0]
        expected_entries = sample_entries
        mock_getUUIDByIdentifier.return_value = "abc".encode("UTF-8")
        # Then
        with self.assertRaises(Continue):
            harvester_2_publications._process_entry(entry, reprocess=False)

    @mock.patch.object(uuid, "uuid4")
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__process_entry_when_new_entry(self, mock_getUUIDByIdentifier, mock_uuid4):
        # Given
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        with gzip.open(filepath, "rt") as fp:
            file_content = [json.loads(line) for line in fp]
        entry_in = file_content[0]
        expected_url = sample_urls_lists[0]
        expected_entry = sample_entries[0]
        expected_filename = sample_filenames[0]
        mock_getUUIDByIdentifier.return_value = None
        mock_uuid4.return_value = sample_uuids[0]
        # When
        url, entry, filename = harvester_2_publications._process_entry(entry_in, reprocess=False)
        # Then
        self.assertIsNotNone(entry["id"])
        self.assertEqual(entry, expected_entry)
        self.assertEqual(url, expected_url)
        self.assertEqual(filename, expected_filename)

    def test__parse_oa_entry(self):
        # Given
        entry_filepath = os.path.join(FIXTURES_PATH, "oa_entry.json")
        with open(entry_filepath, "rt") as fp:
            entry_in = json.load(fp)
        entry_in["id"] = sample_uuids[0]
        expected_urls, expected_entry, expected_filename = parsed_oa_entry_output
        # When
        urls, entry, filename = harvester_2_publications._parse_entry(entry_in)
        # Then
        self.assertEqual(entry, expected_entry)
        self.assertEqual(urls, expected_urls)
        self.assertEqual(filename, expected_filename)

    def test__parse_ca_entry(self):
        # Given
        entry_filepath = os.path.join(FIXTURES_PATH, "ca_entry.json")
        with open(entry_filepath, "rt") as fp:
            entry_in = json.load(fp)
        entry_in["id"] = sample_uuids[0]
        expected_urls, expected_entry, expected_filename = parsed_ca_entry
        # When
        urls, entry, filename = harvester_2_publications._parse_entry(entry_in)
        # Then
        self.assertEqual(entry, expected_entry)
        self.assertEqual(urls, expected_urls)
        self.assertEqual(filename, expected_filename)

    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__check_entry_when_entry_already_processed(self, mock_getUUIDByIdentifier):
        # Given
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        with gzip.open(filepath, "rt") as fp:
            file_content = [json.loads(line) for line in fp]
        entry = file_content[0]
        expected_entries = sample_entries
        mock_getUUIDByIdentifier.return_value = "abc".encode("UTF-8")
        # Then
        with self.assertRaises(Continue):
            _check_entry(
                entry,
                entry["doi"],
                harvester_2_publications.getUUIDByIdentifier,
                reprocess=False,
                env=harvester_2_publications.env,
                env_doi=harvester_2_publications.env_doi,
            )
        # self.assertIsNotNone(entry['id'])

    @mock.patch.object(uuid, "uuid4")
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__check_entry_when_new_entry(self, mock_getUUIDByIdentifier, mock_uuid4):
        # Given
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        with gzip.open(filepath, "rt") as fp:
            file_content = [json.loads(line) for line in fp]
        entry = file_content[0]
        expected_id = sample_uuids[0]
        mock_getUUIDByIdentifier.return_value = None
        mock_uuid4.return_value = expected_id
        # When
        _check_entry(entry, entry["doi"], harvester_2_publications.getUUIDByIdentifier,
                    reprocess=False, env=harvester_2_publications.env,
                    env_doi=harvester_2_publications.env_doi)
        # Then
        self.assertEqual(entry["id"], expected_id)


class ManageFiles(TestCase):
    def setUp(self):
        self.entry = local_entry = sample_entries[0]
        self.DATA_PATH = os.path.join(FIXTURES_PATH, "manageFiles")
        self.filepaths = {
            "dest_path": generateStoragePath(local_entry["id"]),
            "local_filename": os.path.join(self.DATA_PATH, local_entry["id"] + ".pdf"),
            "local_filename_json": os.path.join(self.DATA_PATH, local_entry["id"] + ".json"),
        }

    def test_generate_thumbnails(self):
        # On n'utilise pas thumbnail
        pass

    def test_write_metadata_file(self):
        # Given
        local_filename_json = os.path.join(FIXTURES_PATH, "metadata.json.test")
        # When
        harvester_2_publications._write_metadata_file(local_filename_json, self.entry)
        # Then
        self.assertTrue(os.path.exists(local_filename_json))
        with open(local_filename_json, "r") as f:
            actual_file_content = json.load(f)
        self.assertEqual(self.entry, actual_file_content)
        os.remove(local_filename_json)

    def test_compress_files(self):
        # Given
        # When
        with mock.patch("harvester.OAHarvester.os.remove"):
            harvester_2_publications._compress_files(
                **self.filepaths, local_entry_id=self.entry["id"], compression_suffix=".gz"
            )
        # Then
        for var_name, file in self.filepaths.items():
            if var_name == "dest_path":
                continue
            compressed_file = file + ".gz"
            self.assertTrue(os.path.exists(compressed_file))
            os.remove(compressed_file)

    def test_upload_files(self):
        # Given
        harvester_2_publications.swift = abc
        harvester_2_publications.swift.upload_files_to_swift = mock.MagicMock()
        # When
        harvester_2_publications._upload_files(**self.filepaths)
        # Then
        harvester_2_publications.swift.upload_files_to_swift.assert_called_with(
            harvester_2_publications.storage_publications,
            [
                (
                    self.filepaths["local_filename"],
                    OvhPath(
                        PUBLICATION_PREFIX,
                        self.filepaths["dest_path"],
                        os.path.basename(self.filepaths["local_filename"]),
                    ),
                ),
                (
                    self.filepaths["local_filename_json"],
                    OvhPath(
                        METADATA_PREFIX,
                        self.filepaths["dest_path"],
                        os.path.basename(self.filepaths["local_filename_json"]),
                    ),
                ),
            ],
        )

    @mock.patch("harvester.OAHarvester.shutil.copyfile")
    @mock.patch("harvester.OAHarvester.os.makedirs")
    def test_save_files_locally(self, mock_makedirs, mock_copyfile):
        # Given
        local_dest_path = os.path.join(DATA_PATH, self.filepaths["dest_path"].to_local())
        compression_suffix = ""
        # When
        harvester_2_publications._save_files_locally(
            **self.filepaths, local_entry_id=self.entry["id"], compression_suffix=compression_suffix
        )
        # Then
        mock_makedirs.assert_called_with(local_dest_path, exist_ok=True)
        mock_copyfile.assert_called_with(
            self.filepaths["local_filename_json"],
            os.path.join(local_dest_path, self.entry["id"] + ".json" + compression_suffix),
        )

    @mock.patch("harvester.OAHarvester.os.remove")
    def test_clean_up_files(self, mock_remove):
        # Given
        # When
        harvester_2_publications._clean_up_files(**self.filepaths, local_entry_id=self.entry["id"])
        # Then
        mock_remove.assert_called_with(self.filepaths["local_filename_json"])

    @mock.patch("harvester.OAHarvester.OAHarvester._clean_up_files")
    @mock.patch("harvester.OAHarvester.OAHarvester._save_files_locally")
    @mock.patch("harvester.OAHarvester.OAHarvester._upload_files")
    @mock.patch("harvester.OAHarvester.OAHarvester._compress_files")
    @mock.patch("harvester.OAHarvester.OAHarvester._write_metadata_file")
    def test_manageFiles(self, mock_write_metadata_file, mock_compress_files, mock_upload_files,
                         mock_save_files_locally, mock_clean_up_files):
        # Given
        # When
        harvester_2_publications.manageFiles(self.entry)
        # Then
        mock_write_metadata_file.assert_called()
        if harvester_2_publications.config["compression"]:
            mock_compress_files.assert_called()
        if harvester_2_publications.swift:
            mock_upload_files.assert_called()
        else:
            mock_save_files_locally.assert_called()
        mock_clean_up_files.assert_called()


class Compress(TestCase):
    def test_compress(self):
        # Given
        expected_pdf_file_compressed = pdf_file + ".gz"
        with open(pdf_file, "rb") as f:
            expected_file_content = f.read()
        # When
        compress(pdf_file)
        # Then
        self.assertTrue(os.path.exists(expected_pdf_file_compressed))
        with gzip.open(expected_pdf_file_compressed, "rb") as f:
            actual_file_content = f.read()
        self.assertEqual(expected_file_content, actual_file_content)
        os.remove(expected_pdf_file_compressed)


class UpdateDict(TestCase):
    def test_update_dict(self):
        # Given
        mydict = {"b": [1]}
        expected_dict = {"a": [1], "b": [1, 2]}
        # When
        update_dict(mydict, "a", 1)
        update_dict(mydict, "b", 2)
        # Then
        self.assertDictEqual(mydict, expected_dict)


class GetNthKey(TestCase):
    def test_get_nth_key(self):
        # Given
        mydict = {"a": [1], "b": [1, 2], "c": [1, 2, 3]}
        # Then
        self.assertEqual(get_nth_key(mydict, 0), "a")
        self.assertEqual(get_nth_key(mydict, 1), "b")
        self.assertEqual(get_nth_key(mydict, -1), "c")
        with self.assertRaises(IndexError):
            get_nth_key(mydict, 3)
        with self.assertRaises(IndexError):
            get_nth_key(mydict, -4)


class Download(TestCase):
    @unittest.skip("No config on github")
    def test_wiley_download(self):
        # Given
        urls, local_entry, filename = wiley_parsed_entry
        # When
        result, local_entry = _download_publication(urls, filename, local_entry)
        # Then
        self.assertEqual(result, "success")
        self.assertEqual(local_entry["harvester_used"], "wiley")
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

    @mock.patch("os.path.getsize")
    @mock.patch("harvester.OAHarvester._process_request")
    @mock.patch("harvester.OAHarvester.arXiv_download")
    def test_fallback_download_when_arXiv_download_does_not_work(
        self, mock_arXiv_download, mock_process_request, mock_getsize
    ):
        # Given
        mock_arXiv_download.return_value = "fail"
        mock_getsize.return_value = 0
        urls, local_entry, filename = arXiv_parsed_entry
        # When
        result, _ = _download_publication(urls, filename, local_entry)
        # Then
        mock_process_request.assert_called()
        os.remove(filename)

    @mock.patch("os.path.getsize")
    @mock.patch("harvester.OAHarvester._process_request")
    @mock.patch("harvester.OAHarvester.wiley_curl")
    def test_fallback_download_when_wiley_download_does_not_work(
        self, mock_wiley_curl, mock_process_request, mock_getsize
    ):
        # Given
        mock_wiley_curl.return_value = "fail"
        mock_getsize.return_value = 0
        urls, local_entry, filename = wiley_parsed_entry
        # When
        result, _ = _download_publication(urls, filename, local_entry)
        # Then
        mock_process_request.assert_called()
        os.remove(filename)

    @unittest.skip("No config on github")
    def test_arXiv_download(self):
        # Given
        urls, local_entry, filename = arXiv_parsed_entry
        # When
        result, local_entry = _download_publication(urls, filename, local_entry)
        # Then
        self.assertEqual(result, "success")
        self.assertEqual(local_entry["harvester_used"], "arxiv")
        self.assertTrue(os.path.getsize(filename) > 0)
        os.remove(filename)


class ProcessRequest(TestCase):
    def test_process_request_cairn_in_url(self):
        # Given
        url = "a_cairn_url"
        expected_headers = {"User-Agent": "MESRI-Barometre-de-la-Science-Ouverte"}
        scraper = abc
        scraper.get = mock.MagicMock()
        # When
        _process_request(scraper, url)
        # Then
        scraper.get.assert_called_with(url, headers=expected_headers, timeout_in_seconds=180)

    def test_process_request_standard_url_no_specific_header(self):
        # Given
        url = ""
        scraper = abc
        scraper.get = mock.MagicMock()
        # When
        _process_request(scraper, url)
        # Then
        scraper.get.assert_called_with(url, timeout_in_seconds=180)

    def test_process_request_not_200(self):
        # Given
        url = ""
        scraper = abc
        scraper.get = mock.MagicMock()

        expected_response = mock.MagicMock()
        expected_response.status_code = 400

        scraper.get.return_value = expected_response
        # When
        content = _process_request(scraper, url)
        # Then
        self.assertIsNone(content)

    def test_process_request_200_pdf(self):
        # Given
        url = ""
        scraper = abc
        scraper.get = mock.MagicMock()

        expected_response = mock.MagicMock()
        expected_response.status_code = 200
        expected_response.text = "%PDF-"
        expected_content = "expected_content"
        expected_response.content = expected_content

        scraper.get.return_value = expected_response
        # When
        content = _process_request(scraper, url)
        # Then
        self.assertEqual(content, expected_content)

    @mock.patch("harvester.OAHarvester.BeautifulSoup")
    def test_process_request_200_not_pdf(self, mock_BeautifulSoup):
        # Given
        url = ""
        scraper = abc
        scraper.get = mock.MagicMock()

        expected_response = mock.MagicMock()
        expected_response.status_code = 200
        expected_response.text = "html_content"

        scraper.get.return_value = expected_response
        soup_mock = mock.MagicMock()
        redirect_url = "redirect_url"
        soup_mock.select_one = mock.MagicMock(return_value={"href": redirect_url})
        mock_BeautifulSoup.return_value = soup_mock
        # Copy the function that is called recursively to be able to both use it and mock it
        original_function = _process_request
        with mock.patch("harvester.OAHarvester._process_request") as mock_process_request:
            # When
            original_function(scraper, url)
            # Then
            redirect_n = 1
            mock_process_request.assert_called_with(scraper, redirect_url, redirect_n)

    def test_cloudscrapper_download_timeout(self):
        # Given
        scraper = cloudscraper.create_scraper(interpreter="nodejs")
        # When
        content = _process_request(scraper, timeout_url, n=0, timeout_in_seconds=10)
        # Then
        self.assertIsNone(content)


class HarvesterInit(TestCase):
    @mock.patch("harvester.OAHarvester.swift.Swift")
    @mock.patch.object(OAHarvester, "_init_lmdb")
    def test_OAHarvester_init(self, mock_init_lmdb, mock_Swift):
        # Given
        config_with_swift = config_harvester.copy()
        config_with_swift["swift"] = "yes"
        # When
        harvester = OAHarvester(config_with_swift)
        # Then
        mock_Swift.assert_called_with(config_with_swift)


if __name__ == "__main__":
    unittest.main()
