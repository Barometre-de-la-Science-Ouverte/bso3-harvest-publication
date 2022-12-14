from unittest import TestCase
from unittest.mock import patch

from harvester.exception import FailedRequest
from harvester.wiley_client import WileyClient
from tests.unit_tests.fixtures.harvester_constants import fake_doi, wiley_fake_config, \
    fake_filepath, fake_file_content
from tests.unit_tests.utils import ResponseMock

TESTED_MODULE = 'harvester.wiley_client'


class WileyClientConstructor(TestCase):

    def tearDown(self) -> None:
        WileyClient.clear_instance()

    @patch.object(WileyClient, '_init_session')
    def test_wiley_client_should_be_instantiated_only_one_time(self, mock_init_session):
        # when
        _ = WileyClient(wiley_fake_config)
        _ = WileyClient(wiley_fake_config)
        _ = WileyClient(wiley_fake_config)

        # then
        mock_init_session.assert_called_once_with(wiley_fake_config)


@patch(f'harvester.base_api_client.write_to_file')
class WileyClientTest(TestCase):

    @patch.object(WileyClient, '_init_session')
    @patch.object(WileyClient, 'download_publication')
    def setUp(self, mock_download_publication, mock_init_session):
        WileyClient.clear_instance()
        self.wiley_client = WileyClient(wiley_fake_config)

    def tearDown(self) -> None:
        WileyClient.clear_instance()

    def test_get_publication_base_url_should_correctly_form_the_url_from_wiley_configuration_dict(
            self, mock_write_to_file):
        # given
        expected_publication_base_url = 'https://wiley-publication-url/'

        # when
        actual_publication_base_url = self.wiley_client.publication_base_url

        # then
        self.assertEqual(expected_publication_base_url, actual_publication_base_url)

    def test_get_publication_url_should_format_doi_and_add_it_to_base_url(
            self, mock_write_to_file):
        # given
        expected_publication_url = 'https://wiley-publication-url/fake%2Fdoi'

        # when
        actual_publication_url = self.wiley_client._get_publication_url(fake_doi)

        # then
        self.assertEqual(expected_publication_url, actual_publication_url)

    def test_validate_downloaded_content_and_write_it_response_ok_behavior(
            self, mock_write_to_file):
        # given
        response = ResponseMock(200, fake_file_content)

        # when
        self.wiley_client._validate_downloaded_content_and_write_it(response, fake_doi, fake_filepath)

        # then
        mock_write_to_file.assert_called_once_with(fake_file_content, fake_filepath)

    def test_validate_downloaded_content_and_write_it_should_raise_a_failed_request_exception_when_response_is_not_ok(
            self, mock_write_to_file):
        # given
        status_code = 500
        response = ResponseMock(status_code, fake_file_content)

        # then
        with self.assertRaises(FailedRequest) as cm:
            # when
            self.wiley_client._validate_downloaded_content_and_write_it(response, fake_doi, fake_filepath)

        exception_message = cm.exception.args[0]
        assert 'status code = 500' in exception_message
        assert f'doi = {fake_doi}' in exception_message
        mock_write_to_file.assert_not_called()
