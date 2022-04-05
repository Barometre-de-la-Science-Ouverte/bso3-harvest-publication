import unittest
from unittest import TestCase, mock
from ovh_handler import generateStoragePath, download_files, upload_and_clean_up, glob, os
from tests.unit_tests.fixtures.swift_object import _swift, local_dir, grobid_files_to_upload, softcite_files_to_upload
from infrastructure.storage.swift import Swift
from domain.ovh_path import OvhPath


class OvhHandler(TestCase):

    def test_generateStoragePath(self):
        # Given
        filename = "123456789"
        # When
        prefix = generateStoragePath(filename)
        # Then
        expected_prefix = OvhPath('12', '34', '56', '78', '123456789')
        self.assertEqual(prefix, expected_prefix)

    @mock.patch.object(Swift, "download_files")
    @mock.patch.object(Swift, "get_swift_list")
    def test_download(self, mock_get_swift_list, mock_swift_download_files):
        # Given
        dest_dir = "."
        files = ["file1.pdf", "file2.pdf"]
        mock_get_swift_list.return_value = files
        # When
        download_files(_swift, dest_dir, files)
        # Then
        mock_swift_download_files.assert_called_with(_swift.config['publications_dump'], ["file1.pdf", "file2.pdf"], dest_dir)

    @mock.patch("ovh_handler.os.makedirs")
    @mock.patch("ovh_handler.os.path.exists")
    @mock.patch.object(Swift, "download_files")
    @mock.patch.object(Swift, "get_swift_list")
    def test_download_dir_is_created_when_does_not_exists(self, mock_get_swift_list, mock_swift_download_files, mock_path_exists, mock_makedirs):
        # Given
        dest_dir = "."
        mock_path_exists.return_value = False
        # When
        download_files(_swift, dest_dir, files=[])
        # Then
        mock_makedirs.assert_called_with(dest_dir)
    
    @mock.patch("ovh_handler.os.remove")
    @mock.patch("ovh_handler.glob")
    @mock.patch.object(Swift, "upload_files_to_swift")
    def test_upload(self, mock_upload_files_to_swift, mock_glob, mock_remove):
        # Given
        mock_glob.return_value = local_dir
        local_dir_path = '.'
        upload_files = grobid_files_to_upload + softcite_files_to_upload
        last_file = local_dir[-1]
        # When
        upload_and_clean_up(_swift, local_dir_path)
        # Then
        mock_glob.assert_called_once()
        mock_upload_files_to_swift.assert_called_with(_swift.config['publications_dump'], upload_files)
        mock_remove.assert_called_with(last_file)

# TODO test clients directely
# class SoftciteStep(TestCase):

#     def test_(self):
#         self.assertEqual(1, 2)


# class GrobidStep(TestCase):

#     def test_(self):
#         self.assertEqual(1, 2)


if __name__ == '__main__':
    unittest.main()
