import re
import subprocess
from time import sleep

import cloudscraper
from bs4 import BeautifulSoup
from requests import ConnectTimeout

from application.server.main.logger import get_logger
from config.logger_config import LOGGER_LEVEL
from harvester.exception import EmptyFileContentException
from harvester.file_utils import is_file_not_empty

logger = get_logger(__name__, level=LOGGER_LEVEL)


def _download_publication(urls, filename, local_entry):
    result = 'fail'
    doi = local_entry['doi']
    for url in urls:
        try:
            logger.debug(f"Publication URL to download = {url}. Filename = {filename}")
            if 'arxiv' in url:
                result, harvester_used = arxiv_download(url, filename, doi)
                if result == 'success':
                    break
            elif 'wiley' in url:
                result, harvester_used = wiley_curl(doi, filename)
                if result == 'success':
                    break

            result, harvester_used = standard_download(url, filename, doi)
            break
        except Exception:
            logger.exception(f"Download failed for {url}", exc_info=True)
            harvester_used, url = '', ''

    local_entry['harvester_used'] = harvester_used
    local_entry['url_used'] = url
    return result, local_entry


def arxiv_download(url: str, filepath: str, doi: str) -> (str, str):
    from config.swift_cli_config import init_cmd
    file_path = url_to_path(url)
    logger.debug(f"URL arxiv to Download: Before = {url}. *** After = {file_path}")
    subprocess.check_call(f'{init_cmd} download arxiv_harvesting {file_path} -o {filepath}', shell=True)
    result, harvester_used = 'fail', 'arxiv'
    if is_file_not_empty(filepath):
        result = 'success'
        logger.debug(f"Download {doi} via arXiv_harvesting")
    return result, harvester_used


def wiley_curl(wiley_doi: str, filepath: str) -> (str, str):
    from config.wiley_config import wiley_curl_cmd
    encoded_wiley_doi = wiley_doi.replace('/', '%2F')
    wiley_curl_cmd += f'{encoded_wiley_doi}" -o {filepath}'
    subprocess.check_call(wiley_curl_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    result, harvester_used = 'fail', 'wiley'
    if is_file_not_empty(filepath):
        result = 'success'
        logger.debug(f"Download {wiley_doi} via wiley API")
    return result, harvester_used


def standard_download(url: str, filename: str, doi: str) -> (str, str):
    scraper = cloudscraper.create_scraper(interpreter='nodejs')
    content = _process_request(scraper, url)
    if not content:
        raise EmptyFileContentException(
            f"The PDF content returned by _process_request is empty (standard download). URL = {url}")

    logger.debug(f"Download {doi} via standard request")
    with open(filename, 'wb') as f_out:
        f_out.write(content)
    result, harvester_used = 'success', 'standard'
    return result, harvester_used


def _process_request(scraper, url, n=0, timeout_in_seconds=60):
    try:
        if "cairn" in url:
            headers = {'User-Agent': 'MESRI-Barometre-de-la-Science-Ouverte'}
            file_data = scraper.get(url, headers=headers, timeout=timeout_in_seconds)
        else:
            file_data = scraper.get(url, timeout=timeout_in_seconds)
        if file_data.status_code == 200:
            if file_data.text[:5] == '%PDF-':
                return file_data.content
            elif n < 5:
                soup = BeautifulSoup(file_data.text, 'html.parser')
                if soup.select_one('a#redirect'):
                    redirect_url = soup.select_one('a#redirect')['href']
                    logger.debug('Waiting 5 seconds before following redirect url')
                    sleep(5)
                    logger.debug(f'Retry number {n + 1}')
                    return _process_request(scraper, redirect_url, n + 1)
        else:
            logger.debug(f"Response code is not successful: {file_data.status_code}")
    except ConnectTimeout:
        logger.exception("Connection Timeout", exc_info=True)
        return


def url_to_path(url, ext='.pdf.gz'):
    try:
        _id = re.findall(r"arxiv\.org/pdf/(.*)$", url)[0]
        prefix = "arxiv" if _id[0].isdigit() else _id.split('/')[0]
        filename = url.split('/')[-1]
        yymm = filename[:4]
        return '/'.join([prefix, yymm, filename, filename + ext])
    except:
        logger.exception("Incorrect arXiv url format, could not extract path")
