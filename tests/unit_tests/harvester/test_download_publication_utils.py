import abc
import os
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock, Mock

import cloudscraper

from config import WILEY
from config.harvester_config import config_harvester
from config.path_config import COMPRESSION_EXT, PUBLICATION_EXT
from harvester.download_publication_utils import _process_request, _download_publication, url_to_path, publisher_api_download
from harvester.exception import FailedRequest
from harvester.wiley_client import WileyClient
from tests.unit_tests.fixtures.api_clients import wiley_client_mock, elsevier_client_mock
from tests.unit_tests.fixtures.harvester import timeout_url, wiley_parsed_entry, arXiv_parsed_entry
from tests.unit_tests.fixtures.harvester_constants import wiley_url
from utils.file import _is_valid_file

TESTED_MODULE = 'harvester.download_publication_utils'


class Download(TestCase):

    @patch(f"{TESTED_MODULE}.arxiv_download")
    @patch(f"{TESTED_MODULE}.publisher_api_download")
    @patch(f"{TESTED_MODULE}.standard_download")
    def test_download_publication_standard_download_should_be_used_when_wiley_client_is_none(
            self, mock_standard_download, mock_publisher_api_download, mock_arxiv_download):
        # Given
        fake_doi = 'fake_doi'
        fake_local_entry = {'doi': fake_doi}
        fake_filename = 'fake_filename'
        fake_url = wiley_url
        fake_urls = [fake_url]

        wiley_client = None
        elsevier_client = None

        # When
        _ = _download_publication(fake_urls, fake_filename, fake_local_entry, wiley_client, elsevier_client)

        # Then
        mock_arxiv_download.assert_not_called()
        mock_publisher_api_download.assert_not_called()
        mock_standard_download.assert_called_once_with(fake_url, fake_filename, fake_doi)

    @unittest.skip("No config on github")
    def test_wiley_download(self):
        # Given
        urls, local_entry, filename = wiley_parsed_entry
        wiley_client = WileyClient(config_harvester[WILEY])
        # When
        result, local_entry = _download_publication(urls, filename, local_entry, wiley_client, elsevier_client_mock)
        # Then
        self.assertEqual(result, "success")
        self.assertEqual(local_entry["harvester_used"], "wiley")
        self.assertTrue(_is_valid_file(filename, "pdf"))
        os.remove(filename)

    def test_wiley_download_should_catch_the_exception_raised_by_wiley_client_and_set_result_to_fail(self):
        def my_side_effect(arg1, arg2):
            raise FailedRequest('FailedRequest')

        mock = Mock()
        mock.side_effect = my_side_effect
        wiley_client_mock.download_publication = mock

        # When
        result, harvester_used = publisher_api_download('fake_doi', 'fake_filepath', wiley_client_mock)

        # Then
        assert result == 'fail'
        assert harvester_used == 'wiley'

    def test_arXiv_url_to_path(self):
        # Given
        ext = PUBLICATION_EXT + COMPRESSION_EXT
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

    @patch("os.path.getsize")
    @patch(f'{TESTED_MODULE}._process_request')
    @patch(f'{TESTED_MODULE}.arxiv_download')
    @patch(f'{TESTED_MODULE}.publisher_api_download')
    def test_fallback_download_when_arXiv_download_does_not_work(
            self, mock_wiley_download, mock_arxiv_download, mock_process_request, mock_getsize
    ):
        # Given
        mock_arxiv_download.return_value = ('fail', 'arxiv')
        mock_getsize.return_value = 0
        urls, local_entry, filename = arXiv_parsed_entry

        # When
        result, _ = _download_publication(urls, filename, local_entry, wiley_client_mock, elsevier_client_mock)
        # Then
        mock_process_request.assert_called()
        os.remove(filename)

    @patch('os.path.getsize')
    @patch(f'{TESTED_MODULE}._process_request')
    @patch(f'{TESTED_MODULE}.publisher_api_download')
    def test_fallback_download_when_wiley_download_does_not_work(
            self, mock_wiley_curl, mock_process_request, mock_getsize
    ):
        # Given
        mock_wiley_curl.return_value = ('fail', 'wiley')
        mock_getsize.return_value = 0
        urls, local_entry, filename = wiley_parsed_entry
        # When
        result, _ = _download_publication(urls, filename, local_entry, wiley_client_mock, elsevier_client_mock)
        # Then
        mock_process_request.assert_called()
        os.remove(filename)

    @unittest.skip("No config on github")
    def test_arXiv_download_a_gz_file_and_decompress_it(self):
        # Given
        urls, local_entry, filename = arXiv_parsed_entry
        # When
        # TODO: need to instantiate a correct wiley client and make sure it is instantiated one time
        with patch('harvester.download_publication_utils.decompress') as mock_decompress:
            _download_publication(urls, filename, local_entry, wiley_client_mock, elsevier_client_mock)
            # Then
            mock_decompress.assert_called_with(filename + COMPRESSION_EXT)

    @unittest.skip("No config on github")
    def test_arXiv_download_output_is_pdf(self):
        # Given
        urls, local_entry, filename = arXiv_parsed_entry
        # When
        result, local_entry = _download_publication(urls, filename, local_entry, wiley_client_mock, elsevier_client_mock)
        # Then
        self.assertEqual(result, "success")
        self.assertEqual(local_entry["harvester_used"], "arxiv")
        self.assertTrue(_is_valid_file(filename, "pdf"))
        os.remove(filename)


class ProcessRequest(TestCase):
    def test_process_request_cairn_in_url(self):
        # Given
        url = "a_cairn_url"
        expected_headers = {"User-Agent": "MESRI-Barometre-de-la-Science-Ouverte"}
        scraper = abc
        scraper.get = MagicMock()
        # When
        _process_request(scraper, url)
        # Then
        scraper.get.assert_called_with(url, headers=expected_headers, timeout=60)

    def test_process_request_standard_url_no_specific_header(self):
        # Given
        url = ""
        scraper = abc
        scraper.get = MagicMock()
        # When
        _process_request(scraper, url)
        # Then
        scraper.get.assert_called_with(url, timeout=60)

    def test_process_request_not_200(self):
        # Given
        url = ""
        scraper = abc
        scraper.get = MagicMock()

        expected_response = MagicMock()
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
        scraper.get = MagicMock()

        expected_response = MagicMock()
        expected_response.status_code = 200
        expected_response.text = "%PDF-"
        expected_content = "expected_content"
        expected_response.content = expected_content

        scraper.get.return_value = expected_response
        # When
        content = _process_request(scraper, url)
        # Then
        self.assertEqual(content, expected_content)

    @patch("harvester.download_publication_utils.BeautifulSoup")
    def test_process_request_200_not_pdf(self, mock_BeautifulSoup):
        # Given
        url = ""
        scraper = abc
        scraper.get = MagicMock()

        expected_response = MagicMock()
        expected_response.status_code = 200
        expected_response.text = "html_content"

        scraper.get.return_value = expected_response
        soup_mock = MagicMock()
        redirect_url = "redirect_url"
        soup_mock.select_one = MagicMock(return_value={"href": redirect_url})
        mock_BeautifulSoup.return_value = soup_mock
        # Copy the function that is called recursively to be able to both use it and mock it
        original_function = _process_request
        with patch("harvester.download_publication_utils._process_request") as mock_process_request:
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
