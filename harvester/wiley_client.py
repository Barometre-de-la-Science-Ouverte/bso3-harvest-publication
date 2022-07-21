from datetime import datetime
from time import sleep
import requests

from application.server.main.logger import get_logger
from config import (
    CONFIG_WILEY_TOKEN_KEY,
    CONFIG_WILEY_PUBLICATION_URL_KEY,
)
from config.logger_config import LOGGER_LEVEL
from harvester.exception import FailedRequest
from utils.file import write_to_file
from utils.singleton import Singleton
from harvester.download_publication_utils import SUCCESS_DOWNLOAD, WILEY_HARVESTER

logger = get_logger(__name__, level=LOGGER_LEVEL)


class WileyClient(metaclass=Singleton):
    def __init__(self, config: dict) -> None:
        logger.info("Initializing the Wiley API client")
        self.config = config
        self.curr_window = datetime.now()
        self.curr_window_num_requests = 0
        self.max_num_requests = 1
        self.window_size = 1  # second
        self.publication_base_url = config[CONFIG_WILEY_PUBLICATION_URL_KEY]
        self.session = self._init_session()

    def _init_session(self) -> requests.Session:
        logger.info("Initializing a requests session for Wiley API")
        session = requests.Session()
        header_wiley = {"Wiley-TDM-Client-Token": self.config[CONFIG_WILEY_TOKEN_KEY]}
        session.headers.update(header_wiley)
        # Need to make a first request to the server to initialize the session
        doi_publication_sure_to_succeed = "10.1111/jdv.15719"
        publication_url = self._get_publication_url(doi_publication_sure_to_succeed)
        response = session.get(publication_url)
        if not response.ok or not response.text[:5] == '%PDF-':
            raise FailedRequest(
                f"First request to initialize the session failed.\
                    Make sure the publication {doi_publication_sure_to_succeed} can be downloaded using the Wiley API.\
                    Request status code = {response.status_code}, Response content = {response.content}"
            )
        logger.debug("First request to initialize the session succeeded")
        return session

    def throttle(self, window_span_in_seconds, max_num_request_per_window):
        """Regulate the number of requests to the max number of requests per window"""
        now = datetime.now()
        if (now - self.curr_window).seconds >= window_span_in_seconds:
            self.curr_window = now
            self.curr_window_num_requests = 0

        self.curr_window_num_requests += 1
        if self.curr_window_num_requests > max_num_request_per_window:
            num_window_to_wait = self.curr_window_num_requests // max_num_request_per_window
            wait_time = num_window_to_wait * window_span_in_seconds
            logger.debug(f"Holding request for {wait_time}s")
            extra_padding_time = 0.1
            sleep(wait_time + extra_padding_time)
            self.throttle(self.window_size, self.max_num_requests)

    def download_publication(self, doi: str, filepath: str) -> (str, str):
        """
        Will raise a FailedRequest exception (_validate_downloaded_content) if the status_code
        is different from 200, this exception will be caught in the `_download_publication` function
        """
        self.throttle(self.window_size, self.max_num_requests)
        logger.debug("Downloading publication using Wiley client")
        publication_url = self._get_publication_url(doi)
        response = self.session.get(publication_url)
        self._validate_downloaded_content_and_write_it(response, doi, filepath)
        return SUCCESS_DOWNLOAD, WILEY_HARVESTER

    def _validate_downloaded_content_and_write_it(self, response, doi: str, filepath: str) -> None:
        if response.ok:
            if response.text[:5] == '%PDF-':
                write_to_file(response.content, filepath)
                logger.debug(
                    f"The publication with doi = {doi} was successfully downloaded via Wiley request"
                )

            else:
                raise FailedRequest(f"Not a PDF")
        else:
            raise FailedRequest(
                f"The publication with doi = {doi} download failed via Wiley request. Request status code = {response.status_code}" \
                + f"Response content = {response.content}"
            )

    def _get_publication_url(self, doi: str) -> str:
        doi_encoded = doi.replace("/", "%2F")
        publication_url = self.publication_base_url + doi_encoded
        return publication_url

