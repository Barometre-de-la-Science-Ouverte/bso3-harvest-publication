import argparse
import gzip
import json
import logging
import os
import pickle
import shutil
import subprocess
import tarfile
import magic
import time
import urllib
import uuid
from concurrent.futures import ThreadPoolExecutor
from random import randint, choices
from config.path_config import DATA_PATH

import cloudscraper
from bs4 import BeautifulSoup
import lmdb
import requests
from tqdm import tqdm
from infrastructure.storage import swift
from logger import logger

# init LMDB
map_size = 10 * 1024 * 1024 * 1024
logging.basicConfig(filename='../harvester.log', filemode='w', level=logging.DEBUG)

logging.getLogger("keystoneclient").setLevel(logging.ERROR)
logging.getLogger("swiftclient").setLevel(logging.ERROR)

biblio_glutton_url = None
crossref_base = None
crossref_email = None

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

    def __init__(self, config, thumbnail=False, sample=None):
        self.config = config

        # standard lmdb environment for storing biblio entries by uuid
        self.env = None

        # lmdb environment for storing mapping between doi/pmcid and uuid
        self.env_doi = None

        # lmdb environment for keeping track of failures
        self.env_fail = None

        # boolean indicating if we want to generate thumbnails of front page of PDF 
        self.thumbnail = thumbnail
        self._init_lmdb()

        # if a sample value is provided, indicate that we only harvest the indicated number of PDF
        self.sample = sample

        self.swift = None
        if "swift" in self.config and len(self.config["swift"]) > 0 and "swift_container" in self.config and len(
                self.config["swift_container"]) > 0:
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

        # open in write mode
        envFilePath = os.path.join(DATA_PATH, 'entries')
        self.env = lmdb.open(envFilePath, map_size=map_size)

        envFilePath = os.path.join(DATA_PATH, 'doi')
        self.env_doi = lmdb.open(envFilePath, map_size=map_size)

        envFilePath = os.path.join(DATA_PATH, 'fail')
        self.env_fail = lmdb.open(envFilePath, map_size=map_size)

    def harvestUnpaywall(self, filepath, reprocess=False, filter_out=[]):
        """
        Main method, use the Unpaywall dataset for getting pdf url for Open Access resources, 
        download in parallel PDF, generate thumbnails (if selected), upload resources locally 
        or on OVH and update the json description of the entries
        """
        if 'batch_size' in self.config:
            batch_size_pdf = self.config['batch_size']
        else:
            batch_size_pdf = 100

        # batch size for lmdb commit
        batch_size_lmdb = 10
        n = 0
        i = 0
        urls = []
        entries = []
        filenames = []
        selection = None
        non_oa_entries = 0
        no_url_for_pdf = 0

        count = _count_entries(gzip.open, filepath)

        if self.sample is not None:
            selection = _sample_selection(self.sample, count)

        with gzip.open(filepath, 'rt') as gz:
            for position, line in enumerate(tqdm(gz, total=count)):
                if selection is not None and not position in selection:
                    continue

                if i == batch_size_pdf:
                    self.processBatch(urls, filenames, entries)
                    # reinit
                    i = 0
                    urls = []
                    entries = []
                    filenames = []
                    n += batch_size_pdf

                # one json entry per line
                entry = json.loads(line)
                doi = entry['doi']

                if doi in filter_out:
                    continue

                try:
                    _check_entry(entry, doi, self.getUUIDByIdentifier, reprocess, self.env, self.env_doi)
                except Continue:
                    continue

                latest_observation = entry['oa_details'][get_nth_key(entry['oa_details'], -1)]
                if latest_observation['is_oa']:
                    # if requested, we always prioritize PMC pdf over publisher one for higher chance of successful download
                    if "prioritize_pmc" in self.config and self.config["prioritize_pmc"]:
                        for oa_location in latest_observation['oa_locations']:
                            if oa_location['repository_normalized'] == "PubMed Central" and oa_location['url_for_pdf'] != None:
                                entry['best_oa_location'] = oa_location
                                break
                    
                    for oa_location in latest_observation['oa_locations']:
                        if oa_location['is_best']: 
                            if oa_location['url_for_pdf']:
                                urls.append(oa_location['url_for_pdf'])
                                entries.append({'id': entry['id'], **oa_location})
                                filenames.append(os.path.join(DATA_PATH, entry['id'] + ".pdf"))
                                i += 1
                                break
                            else: #TODO voir s'il faut proposer un url (dans ceux is_best=False)
                                no_url_for_pdf += 1
                                break
                else:
                    non_oa_entries += 1
        # we need to process the latest incomplete batch (if not empty)
        if len(urls) > 0:
            self.processBatch(urls, filenames, entries)
            n += len(urls)

        logging.info(f"number of entries not oa: {non_oa_entries}")
        logging.info(f"number of entries without a valid pdf url: {no_url_for_pdf}")
        logging.info(f"number of entries to be processed: {n}")

    def harvestPMC(self, filepath, reprocess=False):
        """
        Main method for PMC, use the provided PMC list file for getting pdf url for Open Access resources, 
        or download the list file on NIH server if not provided, download in parallel PDF, generate thumbnails, 
        upload resources on S3 and update the json description of the entries
        """
        if 'batch_size' in self.config:
            batch_size_pdf = self.config['batch_size']
        else:
            batch_size_pdf = 100

        pmc_base = self.config['pmc_base']
        # batch size for lmdb commit
        batch_size_lmdb = 10
        n = 0
        i = 0
        urls = []
        entries = []
        filenames = []

        selection = None

        count = _count_entries(open, filepath)
        
        if self.sample is not None:
            selection = _sample_selection(self.sample, count)
        
        with open(filepath, 'rt') as fp:
            position = 0
            for line in tqdm(fp, total=count):
                if selection is not None and not position in selection:
                    position += 1
                    continue

                # skip first line which gives the date when the list has been generated
                if position == 0:
                    position += 1
                    continue

                if i == batch_size_pdf:
                    self.processBatch(urls, filenames, entries)  # , txn, txn_doi, txn_fail)
                    # reinit
                    i = 0
                    urls = []
                    entries = []
                    filenames = []
                    n += batch_size_pdf

                # one PMC entry per line
                print(line)
                tokens = line.split('\t')
                subpath = tokens[0]
                print(tokens)
                pmcid = tokens[2]
                pmid = str(tokens[3])
                ind = pmid.find(":")
                if ind != -1:
                    pmid = pmid[ind + 1:]

                if pmcid is None:
                    position += 1
                    continue

                # check if the entry has already been processed
                if self.getUUIDByIdentifier(pmcid) is not None:
                    position += 1
                    continue

                entry = {}
                entry['pmid'] = pmid
                # TODO: avoid depending on instanciated DOI
                entry['doi'] = pmcid

                try:
                    _check_entry(entry, pmcid, self.getUUIDByIdentifier, reprocess, self.env, self.env_doi)
                except Continue:
                    continue

                if subpath is not None:
                    tar_url = pmc_base + subpath
                    # print(tar_url)
                    urls.append(tar_url)

                    # entry['id'] = str(uuid.uuid4())
                    # entry['pmcid'] = pmcid

                    entry_url = {}
                    entry_url['url_for_pdf'] = tar_url
                    entry['best_oa_location'] = entry_url
                    entries.append(entry)
                    filenames.append(os.path.join(DATA_PATH, entry['id'] + ".tar.gz"))
                    i += 1

                position += 1

        # we need to process the latest incomplete batch (if not empty)
        if len(urls) > 0:
            self.processBatch(urls, filenames, entries)
            n += len(urls)

        print("total processed entries:", n)

    def processBatch(self, urls, filenames, entries):  # , txn, txn_doi, txn_fail):
        with ThreadPoolExecutor(max_workers=12) as executor:
            results = executor.map(_download, urls, filenames, entries, timeout=30)

        # LMDB write transaction must be performed in the thread that created the transaction, so
        # better to have the following lmdb updates out of the paralell process
        entries = []
        for result in results:
            local_entry = result[1]
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

            if (result[0] is None or result[0] == "0" or result[0] == "success") and valid_file:
                # update DB
                with self.env.begin(write=True) as txn:
                    txn.put(local_entry['id'].encode(encoding='UTF-8'),
                            _serialize_pickle(_create_map_entry(local_entry)))

                    # with self.env_doi.begin(write=True) as txn_doi:
                #    txn_doi.put(local_entry['doi'].encode(encoding='UTF-8'), local_entry['id'].encode(encoding='UTF-8'))

                entries.append(local_entry)
            else:
                logger.info("register harvesting failure: " + result[0])

                # update DB
                with self.env.begin(write=True) as txn:
                    txn.put(local_entry['id'].encode(encoding='UTF-8'),
                            _serialize_pickle(_create_map_entry(local_entry)))

                    # with self.env_doi.begin(write=True) as txn_doi:
                #    txn_doi.put(local_entry['doi'].encode(encoding='UTF-8'), local_entry['id'].encode(encoding='UTF-8'))

                with self.env_fail.begin(write=True) as txn_fail:
                    txn_fail.put(local_entry['id'].encode(encoding='UTF-8'), _serialize_pickle({"result": result[0], "url": local_entry['url_for_pdf']}))

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
        with ThreadPoolExecutor(max_workers=12) as executor:
            results = executor.map(self.manageFiles, entries, timeout=30)

    def getUUIDByIdentifier(self, identifier):
        txn = self.env_doi.begin()
        return txn.get(identifier.encode(encoding='UTF-8'))

    def manageFiles(self, local_entry):
        local_filename = os.path.join(DATA_PATH, local_entry['id'] + ".pdf")
        local_filename_nxml = os.path.join(DATA_PATH, local_entry['id'] + ".nxml")

        # for metadata
        local_filename_json = os.path.join(DATA_PATH, local_entry['id'] + ".json")
        # generate thumbnails
        if self.thumbnail:
            try:
                generate_thumbnail(local_filename)
            except:
                logger.exception("error with thumbnail generation: " + local_entry['id'])

        dest_path = os.path.join(generateStoragePath(local_entry['id']), local_entry['id'])

        thumb_file_small = local_filename.replace('.pdf', '-thumb-small.png')
        thumb_file_medium = local_filename.replace('.pdf', '-thumb-medium.png')
        thumb_file_large = local_filename.replace('.pdf', '-thumb-large.png')

        if os.path.isfile(thumb_file_small):
            local_entry["valid_thumbnails"] = True

        # write metadata file
        with open(local_filename_json, 'w') as outfile:
            json.dump(local_entry, outfile)

        compression_suffix = ""
        if self.config["compression"]:
            compression_suffix = ".gz"

            try:
                if os.path.isfile(local_filename):
                    subprocess.check_call(['gzip', '-f', local_filename])
                    local_filename += compression_suffix

                if os.path.isfile(local_filename_nxml):
                    subprocess.check_call(['gzip', '-f', local_filename_nxml])
                    local_filename_nxml += compression_suffix

                if os.path.isfile(local_filename_json):
                    subprocess.check_call(['gzip', '-f', local_filename_json])
                    local_filename_json += compression_suffix

                if self.thumbnail:
                    if os.path.isfile(thumb_file_small):
                        subprocess.check_call(['gzip', '-f', thumb_file_small])
                        thumb_file_small += compression_suffix

                    if os.path.isfile(thumb_file_medium):
                        subprocess.check_call(['gzip', '-f', thumb_file_medium])
                        thumb_file_medium += compression_suffix

                    if os.path.isfile(thumb_file_large):
                        subprocess.check_call(['gzip', '-f', thumb_file_large])
                        thumb_file_large += compression_suffix
            except:
                logger.error("Error compressing resource files for " + local_entry['id'])

        if self.swift is not None:
            # to SWIFT object storage, we can do a bulk upload for all the resources associated to the entry
            try:
                files_to_upload = []
                if os.path.isfile(local_filename):
                    files_to_upload.append(local_filename)
                if os.path.isfile(local_filename_nxml):
                    files_to_upload.append(local_filename_nxml)
                if os.path.isfile(local_filename_json):
                    files_to_upload.append(local_filename_json)

                if self.thumbnail:
                    if os.path.isfile(thumb_file_small):
                        files_to_upload.append(thumb_file_small)

                    if os.path.isfile(thumb_file_medium):
                        files_to_upload.append(thumb_file_medium)

                    if os.path.isfile(thumb_file_large):
                        files_to_upload.append(thumb_file_large)

                if len(files_to_upload) > 0:
                    self.swift.upload_files_to_swift(files_to_upload, dest_path)

            except:
                logger.error("Error writing on SWIFT object storage")
        
        else:
            # save under local storage indicated by data_path in the config json
            try:
                local_dest_path = os.path.join(DATA_PATH, dest_path)

                os.makedirs(local_dest_path, exist_ok=True)
                if os.path.isfile(local_filename):
                    shutil.copyfile(local_filename,
                                    os.path.join(local_dest_path, local_entry['id'] + ".pdf" + compression_suffix))
                if os.path.isfile(local_filename_nxml):
                    shutil.copyfile(local_filename_nxml,
                                    os.path.join(local_dest_path, local_entry['id'] + ".nxml" + compression_suffix))
                if os.path.isfile(local_filename_json):
                    shutil.copyfile(local_filename_json,
                                    os.path.join(local_dest_path, local_entry['id'] + ".json" + compression_suffix))

                if self.thumbnail:
                    if os.path.isfile(thumb_file_small):
                        shutil.copyfile(thumb_file_small, os.path.join(local_dest_path, local_entry[
                            'id'] + "-thumb-small.png") + compression_suffix)

                    if os.path.isfile(thumb_file_medium):
                        shutil.copyfile(thumb_file_medium, os.path.join(local_dest_path, local_entry[
                            'id'] + "-thumb-medium.png") + compression_suffix)

                    if os.path.isfile(thumb_file_large):
                        shutil.copyfile(thumb_file_large, os.path.join(local_dest_path, local_entry[
                            'id'] + "-thumb-larger.png") + compression_suffix)

            except IOError:
                logger.exception("invalid path")

        # clean pdf and thumbnail files
        try:
            if os.path.isfile(local_filename):
                os.remove(local_filename)
            if os.path.isfile(local_filename_nxml):
                os.remove(local_filename_nxml)
            if os.path.isfile(local_filename_json):
                os.remove(local_filename_json)

            # possible tar.gz remaining from PMC resources
            local_filename_tar = os.path.join(DATA_PATH, local_entry['id'] + ".tar.gz")
            if os.path.isfile(local_filename_tar):
                os.remove(local_filename_tar)

            if self.thumbnail:
                if os.path.isfile(thumb_file_small):
                    os.remove(thumb_file_small)
                if os.path.isfile(thumb_file_medium):
                    os.remove(thumb_file_medium)
                if os.path.isfile(thumb_file_large):
                    os.remove(thumb_file_large)
        except IOError:
            logger.exception("temporary file cleaning failed")

    def dump(self, dump_file, fail_file=None):
        """
        Write a catalogue for the harvested Open Access resources, mapping all the OA UUID with strong identifiers
        (doi, pimd, ...). Optionally, write an additional file with only havesting failures for OA entries.
        """

        # init lmdb transactions
        txn = self.env.begin(write=True)

        nb_total = txn.stat()['entries']
        print("number of entries with OA link:", nb_total)

        file_out_fail = None
        if fail_file is not None:
            try:
                file_out_fail = open(fail_file, 'w')
            except:
                logger.exception("Could not open dump file for harvesting fail failure report")

        with open(dump_file, 'w') as file_out:
            # iterate over lmdb
            cursor = txn.cursor()
            for key, value in cursor:
                if txn.get(key) is None:
                    continue
                map_entry = _deserialize_pickle(txn.get(key))
                map_entry["id"] = key.decode(encoding='UTF-8')

                json_local_entry = json.dumps(map_entry)
                file_out.write(json_local_entry)
                file_out.write("\n")

                if file_out_fail is not None:
                    if 'resources' in json_local_entry and not 'pdf' in json_local_entry['resources'] and not 'xml' in \
                                                                                                              json_local_entry[
                                                                                                                  'resources']:
                        file_out_fail.write(json.dumps(map_entry))
                        file_out_fail.write("\n")

        if file_out_fail is not None:
            file_out_fail.close()

        if self.config["compression"]:
            subprocess.check_call(['gzip', '-f', dump_file])
            dump_file += ".gz"
            if fail_file is not None:
                subprocess.check_call(['gzip', '-f', fail_file])
                fail_file += ".gz"

        if self.swift is not None:
            # we back-up existing map file on the SWIFT container
            dump_file_name = os.path.basename(dump_file)
            shutil.move(dump_file, dump_file + ".new")
            try:
                path_for_old = os.path.join(DATA_PATH, dump_file_name + ".old")
                # TBD: check if the file exists to avoid the 404 exception
                self.swift.download_file(dump_file_name, path_for_old)
                self.swift.upload_file_to_swift(path_for_old, None)
            except:
                logger.debug("no map file on SWIFT object storage")
            shutil.move(dump_file + ".new", dump_file)

            # new map file to SWIFT object storage
            try:
                if os.path.isfile(dump_file):
                    self.swift.upload_file_to_swift(dump_file, None)
            except:
                logger.error("Error writing on SWIFT object storage")

        # always save under local storage indicated by data_path in the config json, and backup the previous one
        try:
            # back-up previous map file: rename existing one as .old
            dump_file_name = os.path.basename(dump_file)
            if os.path.isfile(os.path.join(DATA_PATH, dump_file_name)):
                shutil.move(os.path.join(DATA_PATH, dump_file_name),
                            os.path.join(DATA_PATH, dump_file_name + ".old"))

            if os.path.isfile(dump_file):
                shutil.copyfile(dump_file, os.path.join(DATA_PATH, dump_file_name))

        except IOError:
            logger.exception("invalid path")

    def reset(self):
        """
        Remove the local lmdb keeping track of the state of advancement of the harvesting and
        of the failed entries
        """
        # close environments
        self.env.close()
        self.env_doi.close()
        self.env_fail.close()

        envFilePath = os.path.join(DATA_PATH, 'entries')
        shutil.rmtree(envFilePath)

        envFilePath = os.path.join(DATA_PATH, 'doi')
        shutil.rmtree(envFilePath)

        envFilePath = os.path.join(DATA_PATH, 'fail')
        shutil.rmtree(envFilePath)

        # clean any possibly remaining tmp files (.pdf and .png)
        for f in os.listdir(DATA_PATH):
            if f.endswith(".pdf") or f.endswith(".png") or f.endswith(".nxml") or f.endswith(".tar.gz") or f.endswith(
                    ".xml"):
                os.remove(os.path.join(DATA_PATH, f))
            # clean any existing data files  
            path = os.path.join(DATA_PATH, f)
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                except OSError:
                    logger.exception("Error cleaning tmp files")

        # re-init the environments
        self._init_lmdb()

        # if used, SWIFT object storage
        if self.swift is not None:
            try:
                self.swift.remove_all_files()
            except:
                logger.error("Error resetting SWIFT object storage")

    def diagnostic(self):
        """
        Print a report on failures stored during the harvesting process
        """
        txn = self.env.begin(write=True)
        txn_fail = self.env_fail.begin(write=True)
        nb_fails = txn_fail.stat()['entries']
        nb_total = txn.stat()['entries']
        print("number of failed entries with OA link:", nb_fails, "out of", nb_total, "entries")


def _sample_selection(sample, count):
        """
        Random selection corresponding to the requested sample size
        """
        if sample > 0:
            selection = [randint(0, count - 1) for p in range(0, sample)]
            selection.sort()
            return selection
        else:
            raise IndexError('Sample must be greater than 0')


def _check_entry(entry, _id, getUUID_fn, reprocess, env, env_doi):
    """Check if the entry has already been processed"""
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
        print("total entries found: " + str(count))
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


def _download(url, filename, local_entry):
    # optional biblio-glutton look-up
    global biblio_glutton_url
    global crossref_base
    global crossref_email

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

    result = _download_requests(url, filename)
    if result != "success":
        result = _download_wget(url, filename)
    if result != "success":
        result = _download_cloudflare_scraper(url, filename)

    if os.path.isfile(filename) and filename.endswith(".tar.gz"):
        _manage_pmc_archives(filename)

    return result, local_entry

def _process_request(scraper, url):
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


def _download_cloudflare_scraper(url, filename):
    result = "fail"
    try:
        scraper = cloudscraper.create_scraper(interpreter='nodejs')
        content = _process_request(scraper, url)
        with open(filename, 'wb') as f_out:
            f_out.write(content)
            result = "success"
    except Exception:
        logger.exception("Download failed for {0} with CloudScraper".format(url))
    return result


def _download_wget(url, filename):
    """ 
    Normally we first try with Python requests (which handle well compression), then move to a more robust download approach, 
    via external wget.
    The drawback of wget is the compression support. It is uncertain depending on the linux distribution 
    (https://unix.stackexchange.com/a/464375) and experimental. So in the following, we keep compression disable and we
    manage the decompression in a second step after checking the mime type of the downloaded file.
    """
    result = "fail"
    # This is the most robust and reliable way to download files I found with Python... to rely on system wget :)
    # cmd = "wget -c --quiet" + " -O " + filename + ' --connect-timeout=10 --waitretry=10 ' + \
    cmd = "wget -c --quiet" + " -O " + filename + ' --timeout=15 --waitretry=0 --tries=5 --retry-connrefused ' + \
          '--header="User-Agent: ' + _get_random_user_agent() + '" ' + \
          '--header="Accept: application/pdf, text/html;q=0.9,*/*;q=0.8" --header="Accept-Encoding: gzip, deflate" ' + \
          '--no-check-certificate ' + \
          '"' + url + '"'
    # '--compression=auto ' + \

    try:
        result = subprocess.check_call(cmd, shell=True)

        # if the used version of wget does not decompress automatically, the following ensures it is done
        result_compression = _check_compression(filename)
        if not result_compression:
            # decompression failed, or file is invalid
            if os.path.isfile(filename):
                try:
                    os.remove(filename)
                except OSError:
                    logger.exception("Deletion of invalid compressed file failed")
                    result = "fail"
            # ensure cleaning
            if os.path.isfile(filename + '.decompressed'):
                try:
                    os.remove(filename + '.decompressed')
                except OSError:
                    logger.exception("Final deletion of temp decompressed file failed")
        else:
            result = "success"

    except subprocess.CalledProcessError as e:
        logger.exception("error subprocess wget")
        # logger.error("wget command was: " + cmd)
        result = "fail"

    except Exception as e:
        logger.exception("Unexpected error wget process")
        result = "fail"

    return str(result)


def _download_requests(url, filename):
    """ 
    Download with Python requests which handle well compression, but not very robust and bad parallelization
    """
    HEADERS = {"""User-Agent""": _get_random_user_agent()}
    result = "fail"
    try:
        file_data = requests.get(url, allow_redirects=True, headers=HEADERS, verify=False, timeout=30)
        if file_data.status_code == 200:
            with open(filename, 'wb') as f_out:
                f_out.write(file_data.content)
            result = "success"
    except Exception:
        logger.exception("Download failed for {0} with requests".format(url))
    return result


def _download_ftp(url, filename):
    """
    Download with Python urllib.requests ftp file
    """

    result = "fail"

    try:
        with urllib.request.urlopen(url) as r:
            file_data = r.read()
        if file_data is not None:
            with open(filename, 'wb') as f_out:
                f_out.write(file_data.content)
            result = "success"
    except Exception:
        logger.exception("Download failed for {0} with requests".format(url))
    return result


def _check_compression(file):
    """
    check if a file is compressed, if yes decompress and replace by the decompressed version
    """
    if os.path.isfile(file):
        if os.path.getsize(file) == 0:
            return False
        file_type = magic.from_file(file, mime=True)
        if file_type == 'application/gzip':
            success = False
            # decompressed in tmp file
            with gzip.open(file, 'rb') as f_in:
                with open(file + '.decompressed', 'wb') as f_out:
                    try:
                        shutil.copyfileobj(f_in, f_out)
                    except OSError:
                        logger.exception("Decompression file failed")
                    else:
                        success = True
            # replace the file
            if success:
                try:
                    shutil.copyfile(file + '.decompressed', file)
                except OSError:
                    logger.exception("Replacement of decompressed file failed")
                    success = False
            # delete the tmp file
            if os.path.isfile(file + '.decompressed'):
                try:
                    os.remove(file + '.decompressed')
                except OSError:
                    logger.exception("Deletion of temp decompressed file failed")
            return success
        else:
            return True
    return False


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


def _manage_pmc_archives(filename):
    # check if finename exists and we have downloaded an archive rather than a PDF (case ftp PMC)
    if os.path.isfile(filename) and filename.endswith(".tar.gz"):
        try:
            # for PMC we still have to extract the PDF from archive
            # print(filename, "is an archive")
            thedir = os.path.dirname(filename)
            # we need to extract the PDF, the NLM extra file, change file name and remove the tar file
            tar = tarfile.open(filename)
            pdf_found = False
            # this is a unique temporary subdirectory to extract the relevant files in the archive, unique directory is
            # introduced to avoid several files with the same name from different archives to be extracted in the 
            # same place 
            basename = os.path.basename(filename)
            tmp_subdir = basename[0:6]
            for member in tar.getmembers():
                if not pdf_found and member.isfile() and (member.name.endswith(".pdf") or member.name.endswith(".PDF")):
                    member.name = os.path.basename(member.name)
                    # create unique subdirectory
                    if not os.path.exists(os.path.join(thedir, tmp_subdir)):
                        os.mkdir(os.path.join(thedir, tmp_subdir))
                    f = tar.extract(member, path=os.path.join(thedir, tmp_subdir))
                    # print("extracted file:", member.name)
                    # be sure that the file exists (corrupted archives are not a legend)
                    if os.path.isfile(os.path.join(thedir, tmp_subdir, member.name)):
                        os.rename(os.path.join(thedir, tmp_subdir, member.name), filename.replace(".tar.gz", ".pdf"))
                        pdf_found = True
                    # delete temporary unique subdirectory
                    try:
                        shutil.rmtree(os.path.join(thedir, tmp_subdir))
                    except OSError:
                        logger.exception("Deletion of tmp dir failed: " + os.path.join(thedir, tmp_subdir))
                        # break
                if member.isfile() and member.name.endswith(".nxml"):
                    member.name = os.path.basename(member.name)
                    # create unique subdirectory
                    if not os.path.exists(os.path.join(thedir, tmp_subdir)):
                        os.mkdir(os.path.join(thedir, tmp_subdir))
                    f = tar.extract(member, path=os.path.join(thedir, tmp_subdir))
                    # print("extracted file:", member.name)
                    # be sure that the file exists (corrupted archives are not a legend)
                    if os.path.isfile(os.path.join(thedir, tmp_subdir, member.name)):
                        os.rename(os.path.join(thedir, tmp_subdir, member.name), filename.replace(".tar.gz", ".nxml"))
                    # delete temporary unique subdirectory
                    try:
                        shutil.rmtree(os.path.join(thedir, tmp_subdir))
                    except OSError:
                        logger.exception("Deletion of tmp dir failed: " + os.path.join(thedir, tmp_subdir))
            tar.close()
            if not pdf_found:
                logger.warning("no pdf found in archive: " + filename)
            if os.path.isfile(filename):
                try:
                    os.remove(filename)
                except OSError:
                    logger.exception("Deletion of PMC archive file failed: " + filename)
        except Exception as e:
            logger.exception("Unexpected error")
            pass


def generate_thumbnail(pdfFile):
    """
    Generate a PNG thumbnails (3 different sizes) for the front page of a PDF. 
    Use ImageMagick for this.
    """
    thumb_file = pdfFile.replace('.pdf', '-thumb-small.png')
    cmd = 'convert -quiet -density 200 -thumbnail x150 -flatten ' + pdfFile + '[0] ' + thumb_file
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        logger.exception("error thumb-small.png")

    thumb_file = pdfFile.replace('.pdf', '-thumb-medium.png')
    cmd = 'convert -quiet -density 200 -thumbnail x300 -flatten ' + pdfFile + '[0] ' + thumb_file
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        logger.exception("error thumb-small.png")

    thumb_file = pdfFile.replace('.pdf', '-thumb-large.png')
    cmd = 'convert -quiet -density 200 -thumbnail x500 -flatten ' + pdfFile + '[0] ' + thumb_file
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        logger.exception("error thumb-small.png")


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

    # add target OA link
    if 'best_oa_location' in local_entry and 'url_for_pdf' in local_entry['best_oa_location']:
        pdf_url = local_entry['best_oa_location']['url_for_pdf']
        if pdf_url is not None:
            map_entry["oa_link"] = pdf_url

    return map_entry


def generateStoragePath(identifier):
    """
    Convert a file name into a path with file prefix as directory paths:
    123456789 -> 12/34/56/123456789
    """
    return os.path.join(identifier[:2], identifier[2:4], identifier[4:6], identifier[6:8])


def _load_config(path='./config.json'):
    """
    Load the json configuration 
    """
    config_json = open(path).read()
    return json.loads(config_json)


def test():
    harvester = OAHarvester()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open Access PDF fixtures")
    parser.add_argument("--unpaywall", default=None, help="path to the Unpaywall dataset (gzipped)")
    parser.add_argument("--pmc", default=None, help="path to the pmc file list, as available on NIH's site")
    parser.add_argument("--config", default="./config.json", help="path to the config file, default is ./config.json")
    parser.add_argument("--dump", default="map.jsonl",
                        help="write a map with UUID, article main identifiers and available harvested resources")
    parser.add_argument("--reprocess", action="store_true", help="reprocessed failed entries with OA link")
    parser.add_argument("--reset", action="store_true",
                        help="ignore previous processing states, clear the existing storage and re-init the "
                             "harvesting process from the beginning")
    parser.add_argument("--thumbnail", action="store_true",
                        help="generate thumbnail files for the front page of the PDF")
    parser.add_argument("--sample", type=int, default=None, help="Harvest only a random sample of indicated size")

    args = parser.parse_args()

    unpaywall = args.unpaywall
    pmc = args.pmc
    config_path = args.config
    reprocess = args.reprocess
    reset = args.reset
    dump = args.dump
    thumbnail = args.thumbnail
    sample = args.sample

    config = _load_config(config_path)

    # some global variables
    if "biblio_glutton_base" in config and len(config["biblio_glutton_base"].strip()) > 0:
        biblio_glutton_url = _biblio_glutton_url(config["biblio_glutton_base"], None)
    if "crossref_base" in config and len(config["crossref_base"].strip()) > 0:
        crossref_base = config["crossref_base"]
    if "crossref_email" in config and len(config["crossref_email"].strip()) > 0:
        crossref_email = config["crossref_email"]

    harvester = OAHarvester(config=config, thumbnail=thumbnail, sample=sample)

    if reset:
        harvester.reset()

    start_time = time.time()

    if unpaywall is not None:
        harvester.harvestUnpaywall(unpaywall, reprocess)
        harvester.diagnostic()
    elif pmc is not None:
        harvester.harvestPMC(pmc, reprocess)
        harvester.diagnostic()

    runtime = round(time.time() - start_time, 3)
    print("runtime: %s seconds " % runtime)

    if dump is not None:
        harvester.dump(dump)