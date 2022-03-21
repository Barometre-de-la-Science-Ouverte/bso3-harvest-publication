import gzip
import json
import logging
import os
import pickle
import re
import shutil
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from multiprocessing import cpu_count
from random import sample, choices, seed

import cloudscraper
import lmdb
import magic
import requests
import urllib3
from bs4 import BeautifulSoup
from tqdm import tqdm

from config.harvest_strategy_config import oa_harvesting_strategy
from config.path_config import DATA_PATH
from infrastructure.storage import swift
from logger import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.getLogger("keystoneclient").setLevel(logging.ERROR)
logging.getLogger("swiftclient").setLevel(logging.ERROR)

biblio_glutton_url = None
crossref_base = None
crossref_email = None
NB_THREADS = 2 * cpu_count()

"""
Harvester for PDF available in open access. a LMDB index is used to keep track of the harvesting process and
possible failures.  

This version uses the standard ThreadPoolExecutor for parallelizing the download/processing/upload processes. 
Given the limits of ThreadPoolExecutor (input stored in memory, blocking Executor.map until the whole input
is processed and output stored in memory until all input is consumed), it works with batches of PDF of a size 
indicated in the config.json file (default is 100 entries). We are moving from first batch to the second one 
only when the first is entirely processed. The harvesting process is not CPU bounded so using threads is okay. 
"""


class Continue(Exception):
    pass


class OAHarvester(object):

    def __init__(self, config, thumbnail=False, sample=None, sample_seed=None):
        self.config = config

        self.env = None  # standard lmdb env for storing biblio entries by uuid
        self.env_doi = None  # lmdb env for storing mapping between doi/pmcid and uuid
        self.env_fail = None  # lmdb env for keeping track of failures
        self._init_lmdb()  # init db
        self._sample_seed = sample_seed  # sample seed
        self.sample = sample if sample != -1 else None
        self.input_swift = None  # swift
        self.swift = None
        self.batch_size = self.config['batch_size']

        # ovh storage metadata input dump and output publications dump
        self.storage_metadata = config['metadata_dump']
        self.storage_publications = config['publications_dump']

        # condition
        is_swift_config = ("swift" in self.config) and len(self.config["swift"]) > 0
        if is_swift_config:
            self.swift = swift.Swift(self.config)

    def _init_lmdb(self):
        # create the data path if it does not exist 
        if not os.path.isdir(DATA_PATH):
            try:
                os.makedirs(DATA_PATH)
            except OSError:
                logger.exception("Creation of the directory %s failed" % DATA_PATH)
            else:
                logger.debug("Successfully created the directory %s" % DATA_PATH)

        lmdb_size = self.config['lmdb_size_Go'] * 1024 * 1024 * 1024
        # open in write mode
        envFilePath = os.path.join(DATA_PATH, 'entries')
        self.env = lmdb.open(envFilePath, map_size=lmdb_size)

        envFilePath = os.path.join(DATA_PATH, 'doi')
        self.env_doi = lmdb.open(envFilePath, map_size=lmdb_size)

        envFilePath = os.path.join(DATA_PATH, 'fail')
        self.env_fail = lmdb.open(envFilePath, map_size=lmdb_size)

    def harvestUnpaywall(self, filepath, reprocess=False, filter_out=[], destination_dir=''):
        """
        Main method, use the Unpaywall dataset for getting pdf url for Open Access resources, 
        download in parallel PDF, generate thumbnails (if selected), upload resources locally 
        or on OVH and update the json description of the entries
        """
        if 'batch_size' in self.config:
            batch_size_pdf = self.config['batch_size']
        else:
            batch_size_pdf = 100
        logger.debug(f'Filepath in count_entries: {filepath}')
        count = _count_entries(gzip.open, filepath)
        if self.sample:
            selection = _sample_selection(self.sample, count, self._sample_seed)
            current_idx = 0
        batch_gen = self._get_batch_generator(filepath, count, reprocess, batch_size_pdf, filter_out)
        for batch in batch_gen:
            if self.sample:
                n = len(batch)
                batch = _apply_selection(batch, selection, current_idx)
                current_idx += n
            urls = [e[0] for e in batch]
            entries = [e[1] for e in batch]
            filenames = [e[2] for e in batch]
            self.processBatch(urls, filenames, entries, destination_dir)

    def _process_entry(self, entry, reprocess, filter_out=[]):
        doi = entry['doi']
        if doi in filter_out:
            raise Continue
        try:
            _check_entry(entry, doi, self.getUUIDByIdentifier, reprocess, self.env, self.env_doi)
            url, entry, filename = self._parse_entry(entry)
            if url:
                return url, entry, filename
        except Continue:
            raise

    def _parse_entry(self, entry):
        """Parse entry to get url, entry, filename"""
        latest_observation = entry['oa_details'][get_nth_key(entry['oa_details'], -1)]
        if latest_observation['is_oa']:
            urls_for_pdf = {}
            oa_locations = {}
            for oa_location in latest_observation['oa_locations']:
                if ('url_for_pdf' in oa_location) and oa_location['url_for_pdf']:
                    for i, strategy in enumerate(oa_harvesting_strategy):
                        if strategy(oa_location):
                            update_dict(urls_for_pdf, i, oa_location['url_for_pdf'])
                            update_dict(oa_locations, i, oa_location)
                            break
            urls_for_pdf = [url for url_list_idx in sorted(urls_for_pdf) for url in urls_for_pdf[url_list_idx]]
            oa_locations = [oa_location for oa_locations_idx in sorted(oa_locations) for oa_location in
                            oa_locations[oa_locations_idx]]
            if urls_for_pdf and oa_locations:
                return urls_for_pdf, {'id': entry['id'], 'doi': entry['doi'], 'domain': entry['bso_classification'],
                                      "oa_locations": oa_locations}, os.path.join(DATA_PATH, entry['id'] + ".pdf")
        else:  # closed access (via publishers APIs)
            # returns urls, entry, filename to match signature even though we really only care about the doi since we use publishers APIs.
            if entry.get("publisher_normalized") in ["Wiley", "American Geophysical Union"]:
                return [f"https://onlinelibrary.wiley.com/doi/pdfdirect/{entry['doi']}"], {'id': entry['id'],
                                                                                           'doi': entry['doi'],
                                                                                           'domain': entry[
                                                                                               'bso_classification']}, os.path.join(
                    DATA_PATH, entry['id'] + ".pdf")
            elif entry.get("publisher_normalized") == "Springer":
                # return [], {'id': entry['id'], 'doi': entry['doi'], 'domain': entry['bso_classification']}, os.path.join(DATA_PATH, entry['id'] + ".pdf")
                pass
            elif entry.get("publisher_normalized") == "Elsevier":
                # return [], {'id': entry['id'], 'doi': entry['doi'], 'domain': entry['bso_classification']}, os.path.join(DATA_PATH, entry['id'] + ".pdf")
                pass
        raise Continue

    def _get_batch_generator(self, filepath, count, reprocess, batch_size=100, filter_out=[]):
        """Reads gzip file and returns batches of processed entries"""
        batch = []
        with gzip.open(filepath, 'rt', encoding='utf-8') as gz:
            for line in tqdm(gz, total=count):
                try:
                    url, entry, filename = self._process_entry(json.loads(line), reprocess, filter_out)
                    if url:
                        batch.append([url, entry, filename])
                except Continue:
                    continue

                if (len(batch) != 0) and (len(batch) % batch_size == 0):
                    yield batch
                    batch = []
            yield batch

    def processBatch(self, urls, filenames, entries, destination_dir=''):  # , txn, txn_doi, txn_fail):
        with ThreadPoolExecutor(max_workers=NB_THREADS) as executor:
            results = executor.map(_download, urls, filenames, entries, timeout=30)
        # LMDB write transaction must be performed in the thread that created the transaction, so
        # better to have the following lmdb updates out of the paralell process
        entries = []
        for result, local_entry in results:
            # conservative check if the downloaded file is of size 0 with a status code sucessful (code: 0),
            # it should not happen *in theory*
            # and check mime type
            valid_file = False

            local_filename = os.path.join(DATA_PATH, local_entry['id'])
            if os.path.isfile(local_filename + ".pdf"):
                if _is_valid_file(local_filename + ".pdf", "pdf"):
                    valid_file = True
                    local_entry["valid_fulltext_pdf"] = True

            if os.path.isfile(local_filename + ".nxml"):
                if _is_valid_file(local_filename + ".nxml", "xml"):
                    valid_file = True
                    local_entry["valid_fulltext_xml"] = True

            if (result is None or result == "0" or result == "success") and valid_file:
                # logger.info(json.dumps({"Stats": {"is_harvested": True, "entry": local_entry}}))
                # update DB
                with self.env.begin(write=True) as txn:
                    txn.put(local_entry['id'].encode(encoding='UTF-8'),
                            _serialize_pickle(_create_map_entry(local_entry)))

                entries.append(local_entry)
            else:
                # logger.info(json.dumps({"Stats": {"is_harvested": False, "entry": local_entry}}))

                # update DB
                with self.env.begin(write=True) as txn:
                    txn.put(local_entry['id'].encode(encoding='UTF-8'),
                            _serialize_pickle(_create_map_entry(local_entry)))

                with self.env_fail.begin(write=True) as txn_fail:
                    txn_fail.put(local_entry['id'].encode(encoding='UTF-8'),
                                 _serialize_pickle({
                                     "result": result,
                                     "url": local_entry['url_for_pdf'] if 'url_for_pdf' in local_entry else 'no url'
                                 }))

                # if an empty pdf or tar file is present, we clean it
                local_filename = os.path.join(DATA_PATH, local_entry['id'] + ".pdf")
                if os.path.isfile(local_filename):
                    os.remove(local_filename)
                local_filename = os.path.join(DATA_PATH, local_entry['id'] + ".tar.gz")
                if os.path.isfile(local_filename):
                    os.remove(local_filename)
                local_filename = os.path.join(DATA_PATH, local_entry['id'] + ".nxml")
                if os.path.isfile(local_filename):
                    os.remove(local_filename)

        # finally we can parallelize the thumbnail/upload/file cleaning steps for this batch
        destination_dirs = len(entries) * [destination_dir]
        with ThreadPoolExecutor(max_workers=NB_THREADS) as executor:
            results = executor.map(self.manageFiles, entries, destination_dirs, timeout=30)

    def getUUIDByIdentifier(self, identifier):
        with self.env_doi.begin() as txn:
            return txn.get(identifier.encode(encoding='UTF-8'))

    def _compress_files(self, local_filename, local_filename_nxml,
                        local_filename_json, local_entry_id, compression_suffix='.gz', **kwargs):
        try:
            if os.path.isfile(local_filename):
                compress(local_filename)
                os.remove(local_filename)
                local_filename += compression_suffix

            if os.path.isfile(local_filename_nxml):
                compress(local_filename_nxml)
                os.remove(local_filename_nxml)
                local_filename_nxml += compression_suffix

            if os.path.isfile(local_filename_json):
                compress(local_filename_json)
                os.remove(local_filename_json)
                local_filename_json += compression_suffix
        except:
            logger.error("Error compressing resource files for " + local_entry_id)

    def _write_metadata_file(self, local_filename_json, local_entry, **kwargs):
        with open(local_filename_json, 'w') as outfile:
            json.dump(local_entry, outfile)

    def _upload_files(self, local_filename, local_filename_nxml, local_filename_json,
                      thumb_file_small, thumb_file_medium, thumb_file_large, dest_path, **kwargs):
        """Uploads all the resources associated to the entry to SWIFT object storage"""
        try:
            files_to_upload = []
            if os.path.isfile(local_filename):
                self.swift.upload_files_to_swift(self.storage_publications, [
                    (local_filename, os.path.join('publication', dest_path, os.path.basename(local_filename)))])
            if os.path.isfile(local_filename_nxml):
                files_to_upload.append(
                    (local_filename_nxml, os.path.join(dest_path, os.path.basename(local_filename_nxml))))
            if os.path.isfile(local_filename_json):
                self.swift.upload_files_to_swift(self.storage_publications, [
                    (local_filename_json, os.path.join('metadata', dest_path, os.path.basename(local_filename_json)))])
            if len(files_to_upload) > 0:
                self.swift.upload_files_to_swift(self.storage_publications, files_to_upload)
        except Exception as e:
            logger.error('Error when uploading', exc_info=True)

    def _save_files_locally(self, dest_path, local_filename, local_entry_id,
                            local_filename_nxml, local_filename_json, compression_suffix, **kwargs):
        try:
            local_dest_path = os.path.join(DATA_PATH, dest_path)
            os.makedirs(local_dest_path, exist_ok=True)
            if os.path.isfile(local_filename):
                shutil.copyfile(local_filename,
                                os.path.join(local_dest_path, local_entry_id + ".pdf" + compression_suffix))
            if os.path.isfile(local_filename_nxml):
                shutil.copyfile(local_filename_nxml,
                                os.path.join(local_dest_path, local_entry_id + ".nxml" + compression_suffix))
            if os.path.isfile(local_filename_json):
                shutil.copyfile(local_filename_json,
                                os.path.join(local_dest_path, local_entry_id + ".json" + compression_suffix))
        except IOError:
            logger.exception("Invalid path")

    def _clean_up_files(self, local_filename, local_entry_id,
                        local_filename_nxml, local_filename_json, **kwargs):
        try:
            if os.path.isfile(local_filename):
                os.remove(local_filename)
            if os.path.isfile(local_filename_nxml):
                os.remove(local_filename_nxml)
            if os.path.isfile(local_filename_json):
                os.remove(local_filename_json)

            # possible tar.gz remaining from PMC resources
            local_filename_tar = os.path.join(DATA_PATH, local_entry_id + ".tar.gz")
            if os.path.isfile(local_filename_tar):
                os.remove(local_filename_tar)
        except IOError:
            logger.exception("Temporary file cleaning failed")

    def manageFiles(self, local_entry, destination_dir=''):
        if destination_dir != '':
            data_path = os.path.join(DATA_PATH, destination_dir)
        else:
            data_path = DATA_PATH
        filepaths: dict = {
            "dest_path": generateStoragePath(local_entry['id']),
            "local_filename": os.path.join(data_path, local_entry['id'] + ".pdf"),
            "local_filename_nxml": os.path.join(data_path, local_entry['id'] + ".nxml"),
            "local_filename_json": os.path.join(data_path, local_entry['id'] + ".json")
        }
        if destination_dir != '':
            filepaths['dest_path'] = os.path.join(destination_dir, filepaths['dest_path'])
        self._write_metadata_file(filepaths['local_filename_json'], local_entry)
        compression_suffix = ""
        if self.config["compression"]:
            compression_suffix = ".gz"
            self._compress_files(**filepaths, local_entry_id=local_entry['id'], compression_suffix=compression_suffix)
            filepaths = {k: (filepaths[k] + compression_suffix if k != "dest_path" else filepaths[k]) for k in
                         filepaths}
        if self.swift:
            self._upload_files(**filepaths)

        else:
            self._save_files_locally(**filepaths, local_entry_id=local_entry['id'],
                                     compression_suffix=compression_suffix)
        self._clean_up_files(**filepaths, local_entry_id=local_entry['id'])

    def diagnostic(self):
        """
        Log a report on failures stored during the harvesting process
        """
        with self.env_fail.begin(write=True) as txn_fail:
            nb_fails = txn_fail.stat()['entries']
        with self.env.begin(write=True) as txn:
            nb_total = txn.stat()['entries']
        logger.info(f"number of failed entries with OA link: {nb_fails} out of {nb_total} entries")
        print(f"number of failed entries with OA link: {nb_fails} out of {nb_total} entries")


def update_dict(mydict, key, value):
    if key in mydict:
        mydict[key].append(value)
    else:
        mydict[key] = [value]


def compress(file):
    deflated_file = file + '.gz'
    with open(file, 'rb') as f_in:
        with gzip.open(deflated_file, 'wb') as f_out:
            f_out.write(f_in.read())


def _sample_selection(nb_samples, count, sample_seed):
    """
        Random selection corresponding to the requested sample size
        """
    if 0 < nb_samples < count:
        seed(sample_seed)
        selection = sample(range(count), nb_samples)
        selection.sort()
        return selection
    else:
        raise IndexError('Sample must be greater than 0 and less than the total number of items to sample from')


def _apply_selection(batch, selection, current_idx):
    sub_selection = [i - current_idx for i in selection if current_idx <= i < current_idx + len(batch)]
    return [batch[i] for i in sub_selection]


def _check_entry(entry, _id, getUUID_fn, reprocess, env, env_doi):
    """Check if the entry has already been processed, reprocessed if needed otherwise create an uuid for the new entry"""
    id_candidate = getUUID_fn(_id)
    if id_candidate is not None:
        id_candidate = id_candidate.decode("utf-8")
        if reprocess:
            entry['id'] = id_candidate
            # did we succeed with this entry?
            with env.begin() as txn:
                local_object = txn.get(id_candidate.encode(encoding='UTF-8'))
                if local_object is not None:
                    local_entry = _deserialize_pickle(local_object)
                    if local_entry is not None:
                        if "resources" in local_entry and "pdf" in local_entry["resources"]:
                            # we have a PDF, so no need to reprocess and we skip
                            raise Continue()
            # otherwise we consider the entry for reprocessing
        else:
            # we don't reprocess existing entries
            raise Continue()
    else:
        # store a UUID
        entry['id'] = str(uuid.uuid4())
        with env_doi.begin(write=True) as txn_doi:
            txn_doi.put(entry['doi'].encode(encoding='UTF-8'), entry['id'].encode(encoding='UTF-8'))


def _biblio_glutton_lookup(biblio_glutton_url, doi=None, pmcid=None, pmid=None, istex_id=None, istex_ark=None,
                           crossref_base=None, crossref_email=None):
    """
    Lookup on biblio_glutton with the provided strong identifiers, return the full agregated biblio_glutton record.
    This allows to optionally enrich downloaded article with Glutton's aggregated metadata. 
    """
    if biblio_glutton_url == None:
        return None

    success = False
    jsonResult = None

    if doi is not None and len(doi) > 0:
        try:
            response = requests.get(biblio_glutton_url, params={'doi': doi}, verify=False, timeout=5)
            success = (response.status_code == 200)
            if success:
                jsonResult = response.json()
        except:
            logger.exception("Could not connect to biblio-glutton for DOI look-up")

    if not success and pmid is not None and len(str(pmid)) > 0:
        try:
            response = requests.get(biblio_glutton_url + "pmid=" + str(pmid), verify=False, timeout=5)
            success = (response.status_code == 200)
            if success:
                jsonResult = response.json()
        except:
            logger.exception("Could not connect to biblio-glutton for PMID look-up")

    if not success and pmcid is not None and len(pmcid) > 0:
        try:
            response = requests.get(biblio_glutton_url + "pmc=" + pmcid, verify=False, timeout=5)
            success = (response.status_code == 200)
            if success:
                jsonResult = response.json()
        except:
            logger.exception("Could not connect to biblio-glutton for PMC ID look-up")

    if not success and istex_id is not None and len(istex_id) > 0:
        try:
            response = requests.get(biblio_glutton_url + "istexid=" + istex_id, verify=False, timeout=5)
            success = (response.status_code == 200)
            if success:
                jsonResult = response.json()
        except:
            logger.exception("Could not connect to biblio-glutton for ISTEX ID look-up")

    if not success and doi is not None and len(doi) > 0 and crossref_base is not None:
        # let's call crossref as fallback for possible X-months gap in biblio-glutton
        # https://api.crossref.org/works/10.1037/0003-066X.59.1.29
        if crossref_email != None:
            user_agent = {
                'User-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0 (mailto:' + crossref_email + ')'}
        else:
            user_agent = {'User-agent': _get_random_user_agent()}
        try:
            response = requests.get(crossref_base + "/works/" + doi, headers=user_agent, verify=False, timeout=5)
            if response.status_code == 200:
                jsonResult = response.json()['message']
                # filter out references and re-set doi, in case there are obtained via crossref
                if "reference" in jsonResult:
                    del jsonResult["reference"]
            else:
                success = False
                jsonResult = None
        except:
            logger.exception("Could not connect to CrossRef")

    return jsonResult


def _get_random_user_agent():
    """
    This is a simple random/rotating user agent covering different devices and web clients/browsers
    Note: rotating the user agent without rotating the IP address (via proxies) might not be a good idea if the same server
    is harvested - but in our case we are harvesting a large variety of different Open Access servers
    """
    user_agents = ["Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0",
                   "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"]
    weights = [0.2, 0.3, 0.5]
    user_agent = choices(user_agents, weights=weights, k=1)

    return user_agent[0]


def _serialize_pickle(a):
    return pickle.dumps(a)


def _deserialize_pickle(serialized):
    return pickle.loads(serialized)


def _count_entries(open_fn, filepath):
    """Check the overall number of entries based on the line number"""
    print("\ncalculating number of entries...")
    count = 0
    if os.path.exists(filepath):
        with open_fn(filepath, 'rb') as fp:
            while 1:
                buffer = fp.read(8192 * 1024)
                if not buffer:
                    break
                count += buffer.count(b'\n')
        return count
    else:
        raise FileNotFoundError(f'{filepath} does not exist')


def get_nth_key(dictionary, n=0):
    if n < 0:
        n += len(dictionary)
    for i, key in enumerate(dictionary.keys()):
        if i == n:
            return key
    raise IndexError("dictionary index out of range")


def _download(urls, filename, local_entry):
    # optional biblio-glutton look-up
    global biblio_glutton_url
    global crossref_base
    global crossref_email
    result = _download_publication(urls, filename, local_entry)

    if biblio_glutton_url is not None:
        local_doi = None
        if "doi" in local_entry:
            local_doi = local_entry['doi']
        local_pmcid = None
        if "pmicd" in local_entry:
            local_pmcid = local_entry['pmicd']
        local_pmid = None
        if "pmid" in local_entry:
            local_pmid = local_entry['pmid']
        glutton_record = _biblio_glutton_lookup(biblio_glutton_url,
                                                doi=local_doi,
                                                pmcid=local_pmcid,
                                                pmid=local_pmid,
                                                crossref_base=crossref_base,
                                                crossref_email=crossref_email)
        if glutton_record is not None:
            local_entry["glutton"] = glutton_record
            if not "doi" in local_entry and "doi" in glutton_record:
                local_entry["doi"] = glutton_record["doi"]
            if not "pmid" in local_entry and "pmid" in glutton_record:
                local_entry["pmid"] = glutton_record["pmid"]
            if not "pmcid" in local_entry and "pmcid" in glutton_record:
                local_entry["pmcid"] = glutton_record["pmcid"]
            if not "istexId" in local_entry and "istexId" in glutton_record:
                local_entry["istexId"] = glutton_record["istexId"]

    return result, local_entry


def _process_request(scraper, url):
    if "cairn" in url:
        headers = {'User-Agent': 'MESRI-Barometre-de-la-Science-Ouverte'}
        file_data = scraper.get(url, headers=headers)
    else:
        file_data = scraper.get(url)
    if file_data.status_code == 200:
        if file_data.text[:5] == '%PDF-':
            return file_data.content
        else:
            soup = BeautifulSoup(file_data.text, 'html.parser')
            if soup.select_one('a#redirect'):
                redirect_url = soup.select_one('a#redirect')['href']
                return _process_request(scraper, redirect_url)
    return


def wiley_curl(wiley_doi, filename):
    from config.wiley_config import wiley_curl_cmd
    wiley_doi = wiley_doi.replace('/', '%2F')
    wiley_curl_cmd += f'{wiley_doi}" -o {filename}'
    subprocess.check_call(wiley_curl_cmd, shell=True)


def url_to_path(url, ext='.pdf.gz'):
    try:
        _id = re.findall(r"arxiv\.org/pdf/(.*)$", url)[0]
        prefix = "arxiv" if _id[0].isdigit() else _id.split('/')[0]
        filename = url.split('/')[-1]
        yymm = filename[:4]
        return '/'.join([prefix, yymm, filename, filename + ext])
    except:
        logger.exception("Incorrect arXiv url format, could not extract path")


def arXiv_download(url, filename):
    from config.arXiv_config import init_cmd
    file_path = url_to_path(url)
    subprocess.check_call(f'{init_cmd} download arxiv_harvesting {file_path} -o {filename}', shell=True)


def _download_publication(urls, filename, local_entry):
    result = "fail"
    for url in urls:
        try:
            if 'arxiv' in url:
                arXiv_download(url, filename)
                if os.path.getsize(filename) > 0:
                    logger.debug(f"Download {local_entry['doi']} via arXiv_harvesting")
                    result = "success"
                    break
            elif 'wiley' in url:
                wiley_curl(local_entry['doi'], filename)
                if os.path.getsize(filename) > 0:
                    logger.debug(f"Download {local_entry['doi']} via wiley API")
                    result = "success"
                    break
            elif 'springer' in url:
                pass
            elif 'elsevier' in url:
                pass
            scraper = cloudscraper.create_scraper(interpreter='nodejs')
            content = _process_request(scraper, url)
            if content:
                logger.debug(f"Download {local_entry['doi']} via standard request")
                with open(filename, 'wb') as f_out:
                    f_out.write(content)
                result = "success"
                break
        except Exception:
            logger.exception(f"Download failed for {url}")
    return result


def _is_valid_file(file, mime_type):
    target_mime = []
    if mime_type == 'xml':
        target_mime.append("application/xml")
        target_mime.append("text/xml")
    elif mime_type == 'png':
        target_mime.append("image/png")
    else:
        target_mime.append("application/" + mime_type)
    file_type = ""
    if os.path.isfile(file):
        if os.path.getsize(file) == 0:
            return False
        file_type = magic.from_file(file, mime=True)
    return file_type in target_mime


def _biblio_glutton_url(biblio_glutton_base, biblio_glutton_port):
    if biblio_glutton_base.endswith("/"):
        res = biblio_glutton_base[:-1]
    else:
        res = biblio_glutton_base
    if biblio_glutton_port is not None and len(biblio_glutton_port) > 0:
        res += ":" + biblio_glutton_port
    return res + "/service/lookup?"


def _create_map_entry(local_entry):
    """
    Create a simple map JSON from the full metadata entry, to be stored locally and for the dumping the JSONL map file
    """
    map_entry = {}
    map_entry["id"] = local_entry["id"]
    if "doi" in local_entry:
        map_entry["doi"] = local_entry["doi"]
    if "pmid" in local_entry:
        map_entry["pmid"] = local_entry["pmid"]
    if "pmcid" in local_entry:
        map_entry["pmcid"] = local_entry["pmcid"]
    if "istexId" in local_entry:
        map_entry["istexId"] = local_entry["istexId"]
    if "ark" in local_entry:
        map_entry["ark"] = local_entry["ark"]
    if "pii" in local_entry:
        map_entry["pii"] = local_entry["pii"]

    resources = ["json"]

    if "valid_fulltext_pdf" in local_entry and local_entry["valid_fulltext_pdf"]:
        resources.append("pdf")
    if "valid_fulltext_xml" in local_entry and local_entry["valid_fulltext_xml"]:
        resources.append("xml")

    if "valid_thumbnails" in local_entry and local_entry["valid_thumbnails"]:
        resources.append("thumbnails")

    map_entry["resources"] = resources
    map_entry["harvested_date"] = date.today().strftime('%Y-%m-%d')
    # add target OA link
    if 'best_oa_location' in local_entry and 'url_for_pdf' in local_entry['best_oa_location']:
        pdf_url = local_entry['best_oa_location']['url_for_pdf']
        if pdf_url is not None:
            map_entry["oa_link"] = pdf_url

    return map_entry


def generateStoragePath(identifier):
    """
    Convert a file name into a path with file prefix as directory paths:
    123456789 -> 12/34/56/78/123456789
    """
    return os.path.join(identifier[:2], identifier[2:4], identifier[4:6], identifier[6:8], identifier)
