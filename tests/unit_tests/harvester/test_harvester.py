import abc
import gzip
import json
import os
import unittest
from unittest import TestCase, mock

from config.path_config import (COMPRESSION_EXT, DATA_PATH, METADATA_EXT,
                                PUBLICATION_EXT)
from harvester.OAHarvester import (METADATA_PREFIX, PUBLICATION_PREFIX,
                                   Continue, OAHarvester, OvhPath,
                                   _check_entry, _count_entries,
                                   generateStoragePath, get_latest_publication,
                                   update_dict, uuid)
from tests.unit_tests.fixtures.api_clients import (elsevier_client_mock,
                                                   wiley_client_mock)
from tests.unit_tests.fixtures.harvester import (FIXTURES_PATH,
                                                 config_harvester,
                                                 harvester_2_publications,
                                                 parsed_ca_entry_elsevier,
                                                 parsed_ca_entry_wiley,
                                                 parsed_oa_entry_output,
                                                 pdf_file, pdf_gz_file,
                                                 sample_entries,
                                                 sample_filenames,
                                                 sample_urls_lists,
                                                 sample_uuids)
from utils.file import compress, decompress


class CountEntries(TestCase):
    def test_when_wrong_filepath_raise_FileNotFoundError_exception(self):
        wrong_filepath = "wrong_filepath"

        with self.assertRaises(FileNotFoundError):
            _count_entries(open, wrong_filepath)

    def test_when_2_publications_then_return_2(self):
        filepath_2_publications = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")

        nb_publications = _count_entries(gzip.open, filepath_2_publications)

        self.assertEqual(nb_publications, 2)

class HarvestUnpaywall(TestCase):
    def test_when_wrong_filepath_raise_FileNotFoundError_exception(self):
        wrong_filepath = "wrong_filepath"

        with self.assertRaises(FileNotFoundError):
            harvester_2_publications.harvestUnpaywall(wrong_filepath)

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
    def test__get_batch_generator_last_batch(self, mock_getUUIDByIdentifier, mock_uuid4):
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
        batch_gen = harvester_2_publications._get_batch_generator(
            filepath, count, reprocess, batch_size
        )
        # Then
        for i, batch in enumerate(batch_gen):
            urls = [e[0] for e in batch]
            entries = [e[1] for e in batch]
            filenames = [e[2] for e in batch]
            self.assertEqual(urls, expected_urls[i * batch_size: (i + 1) * batch_size])
            self.assertEqual(entries, expected_entries[i * batch_size: (i + 1) * batch_size])
            self.assertEqual(filenames, expected_filenames[i * batch_size: (i + 1) * batch_size])

    @mock.patch.object(uuid, "uuid4")
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__get_batch_generator(self, mock_getUUIDByIdentifier, mock_uuid4):
        # Given
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        count = _count_entries(gzip.open, filepath)
        reprocess = False
        batch_size = 1
        expected_urls = sample_urls_lists
        expected_filenames = sample_filenames
        expected_entries = sample_entries
        mock_getUUIDByIdentifier.return_value = None
        mock_uuid4.side_effect = sample_uuids
        # When
        batch_gen = harvester_2_publications._get_batch_generator(
            filepath, count, reprocess, batch_size
        )
        # Then
        for i, batch in enumerate(batch_gen):
            urls = [e[0] for e in batch]
            entries = [e[1] for e in batch]
            filenames = [e[2] for e in batch]
            self.assertEqual(urls, expected_urls[i * batch_size: (i + 1) * batch_size])
            self.assertEqual(entries, expected_entries[i * batch_size: (i + 1) * batch_size])
            self.assertEqual(filenames, expected_filenames[i * batch_size: (i + 1) * batch_size])

    @mock.patch.object(uuid, "uuid4")
    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    @mock.patch.object(OAHarvester, "_process_entry", mock.Mock(side_effect=Continue()))
    def test__get_batch_generator_Continue(self, mock_getUUIDByIdentifier, mock_uuid4):
        # Given
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        count = _count_entries(gzip.open, filepath)
        reprocess = False
        batch_size = 1
        mock_getUUIDByIdentifier.return_value = None
        mock_uuid4.side_effect = sample_uuids
        # When
        batch_gen = harvester_2_publications._get_batch_generator(
            filepath, count, reprocess, batch_size
        )
        # Then
        for i, batch in enumerate(batch_gen):
            self.assertEqual(batch, [])

    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__process_entry_when_entry_already_processed(self, mock_getUUIDByIdentifier):
        # Given
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        with gzip.open(filepath, "rt") as fp:
            file_content = [json.loads(line) for line in fp]
        entry = file_content[0]
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

    def test__parse_ca_entry_Wiley(self):
        # Given
        entry_filepath = os.path.join(FIXTURES_PATH, "ca_entry_wiley.json")
        with open(entry_filepath, "rt") as fp:
            entry_in = json.load(fp)
        entry_in["id"] = sample_uuids[0]
        expected_urls, expected_entry, expected_filename = parsed_ca_entry_wiley
        # When
        urls, entry, filename = harvester_2_publications._parse_entry(entry_in)
        # Then
        self.assertEqual(entry, expected_entry)
        self.assertEqual(urls, expected_urls)
        self.assertEqual(filename, expected_filename)

    def test__parse_ca_entry_Elsevier(self):
        # Given
        entry_filepath = os.path.join(FIXTURES_PATH, "ca_entry_elsevier.json")
        with open(entry_filepath, "rt") as fp:
            entry_in = json.load(fp)
        entry_in["id"] = sample_uuids[0]
        expected_urls, expected_entry, expected_filename = parsed_ca_entry_elsevier
        # When
        urls, entry, filename = harvester_2_publications._parse_entry(entry_in)
        # Then
        self.assertEqual(entry, expected_entry)
        self.assertEqual(urls, expected_urls)
        self.assertEqual(filename, expected_filename)

    def test__parse_entry_Continue(self):
        # Given a CA publication that is neither wiley nor elsevier
        entry_filepath = os.path.join(FIXTURES_PATH, "ca_entry_continue.json")
        with open(entry_filepath, "rt") as fp:
            entry_in = json.load(fp)
        entry_in["id"] = sample_uuids[0]
        # Then
        with self.assertRaises(Continue):
            # When
            harvester_2_publications._parse_entry(entry_in)

    @mock.patch.object(OAHarvester, "getUUIDByIdentifier")
    def test__check_entry_when_entry_already_processed(self, mock_getUUIDByIdentifier):
        # Given
        filepath = os.path.join(FIXTURES_PATH, "dump_2_publications.jsonl.gz.test")
        with gzip.open(filepath, "rt") as fp:
            file_content = [json.loads(line) for line in fp]
        entry = file_content[0]
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
        _check_entry(
            entry,
            entry["doi"],
            harvester_2_publications.getUUIDByIdentifier,
            reprocess=False,
            env=harvester_2_publications.env,
            env_doi=harvester_2_publications.env_doi,
        )
        # Then
        self.assertEqual(entry["id"], expected_id)


class ManageFiles(TestCase):
    def setUp(self):
        self.entry = local_entry = sample_entries[0]
        self.DATA_PATH = os.path.join(FIXTURES_PATH, "manageFiles")
        self.filepaths = {
            "dest_path": generateStoragePath(local_entry["id"]),
            "local_filename": os.path.join(self.DATA_PATH, local_entry["id"] + PUBLICATION_EXT),
            "local_filename_json": os.path.join(self.DATA_PATH, local_entry["id"] + METADATA_EXT),
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
                **self.filepaths, local_entry_id=self.entry["id"], compression_suffix=COMPRESSION_EXT
            )
        # Then
        for var_name, file in self.filepaths.items():
            if var_name == "dest_path":
                continue
            compressed_file = file + COMPRESSION_EXT
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
            os.path.join(local_dest_path, self.entry["id"] + METADATA_EXT + compression_suffix),
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
    def test_manageFiles(
            self,
            mock_write_metadata_file,
            mock_compress_files,
            mock_upload_files,
            mock_save_files_locally,
            mock_clean_up_files,
    ):
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

    def test_decompress(self):
        # Given
        expected_pdf_file = os.path.splitext(pdf_gz_file)[0]
        with gzip.open(pdf_gz_file, "rb") as f:
            expected_file_content = f.read()
        # When
        decompress(pdf_gz_file)
        # Then
        self.assertTrue(os.path.exists(expected_pdf_file))
        with open(expected_pdf_file, "rb") as f:
            actual_file_content = f.read()
        self.assertEqual(expected_file_content, actual_file_content)
        os.remove(expected_pdf_file)


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


class GetLatestPublication(TestCase):
    def test_get_latest_publication(self):
        # Given
        publication_metadata = {
            "oa_details": {
                "2019": {"b"},
                "2020": {"c"},
                "2021": {"d"},
                "2021Q1": {"e"},
                "2021Q4": {"f"},
            }
        }
        expected_publication = {"f"}

        # When
        latest_publication = get_latest_publication(publication_metadata)
        # Then
        self.assertEqual(latest_publication, expected_publication)


class HarvesterInit(TestCase):
    @mock.patch("harvester.OAHarvester.swift.Swift")
    @mock.patch.object(OAHarvester, "_init_lmdb")
    def test_OAHarvester_init(self, mock_init_lmdb, mock_Swift):
        # Given
        config_with_swift = config_harvester.copy()
        config_with_swift["swift"] = "yes"
        # When
        _ = OAHarvester(config_with_swift, wiley_client_mock, elsevier_client_mock)
        # Then
        mock_Swift.assert_called_with(config_with_swift)


if __name__ == "__main__":
    unittest.main()
