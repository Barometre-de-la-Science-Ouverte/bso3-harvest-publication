import shutil
from typing import List

from swiftclient.service import SwiftError, SwiftService, SwiftUploadObject

from application.server.main.logger import get_logger
from config.harvester_config import config_harvester
from logger import logger

METADATA_DUMP = config_harvester['metadata_dump']
PUBLICATIONS_DUMP = config_harvester['publications_dump']

logger = get_logger(__name__)


class Swift(object):

    def __init__(self, config):
        self.config = config
        options = self._init_swift_options()

        options['object_uu_threads'] = 20
        self.swift = SwiftService(options=options)
        container_names = []
        try:
            list_account_part = self.swift.list()
            for page in list_account_part:
                if page["success"]:
                    for item in page["listing"]:
                        i_name = item["name"]
                        container_names.append(i_name)
                        if i_name == METADATA_DUMP:
                            print("using input SWIFT", METADATA_DUMP, "container:", item)
                        elif i_name == PUBLICATIONS_DUMP:
                            print("using output SWIFT", PUBLICATIONS_DUMP, "container:", item)
                else:
                    logger.error("error listing SWIFT object storage containers")

        except SwiftError as e:
            logger.exception("error listing containers")

        if PUBLICATIONS_DUMP not in container_names:
            # create the container
            try:
                self.swift.post(container=PUBLICATIONS_DUMP)
            except SwiftError:
                logger.exception(
                    "error creating SWIFT object storage container " + PUBLICATIONS_DUMP)
        else:
            logger.debug("container already exists on SWIFT object storage: " + PUBLICATIONS_DUMP)

    def _init_swift_options(self):
        options = {}
        for key in self.config["swift"]:
            if self.config["swift"][key] and len(self.config["swift"][key].strip()) > 0:
                options[key] = self.config["swift"][key]
        return options

    def upload_files_to_swift(self, container, file_path_dest_path_tuples:List):
        """
        Bulk upload of a list of files to current SWIFT object storage container under the same destination path
        """
        print("start upload_files_to_swift")
        # Slightly modified to be able to upload to more than one dest_path
        objs = [SwiftUploadObject(file_path, object_name=dest_path) for file_path, dest_path in file_path_dest_path_tuples]
        # for file_path, dest_path in file_path_dest_path_tuples:
        #     logger.info(f"Uploading {file_path} to {container} at {dest_path}")
        try:
            print("upload_files_to_swift checkpoint 1")
            for result in self.swift.upload(container, objs):
                print("upload_files_to_swift checkpoint start for")
                if not result['success']:
                    print("upload_files_to_swift checkpoint error")
                    error = result['error']
                    if result['action'] == "upload_object":
                        logger.error("Failed to upload object %s to container %s: %s" % (
                            container, result['object'], error))
                    else:
                        logger.error("%s" % error)
                else:
                    print("upload_files_to_swift checkpoint success")
                    logger.info(f'Object: {result["path"]} has been uploaded on {container} at {result["object"]}')
        except SwiftError as e:
            print(e)
            logger.exception("error uploading file to SWIFT container")

    def remove_all_files(self, container):
        """
        Remove all the existing files on the SWIFT object storage
        """
        try:
            list_parts_gen = self.swift.list(container=container)
            for page in list_parts_gen:
                if page["success"]:
                    to_delete = []
                    for item in page["listing"]:
                        to_delete.append(item["name"])
                    for del_res in self.swift.delete(container=container, objects=to_delete):
                        if not del_res['success']:
                            error = del_res['error']
                            if del_res['action'] == "delete_object":
                                logger.error("Failed to delete object %s from container %s: %s" % (
                                    container, del_res['object'], error))
                            else:
                                logger.error("%s" % error)
        except SwiftError:
            logger.exception("error removing all files from SWIFT container")

    def download_files(self, container, file_path, dest_path):
        """
        Download a file given a path and returns the download destination file path.
        """
        logger.debug(f'Downloading {file_path} from container {container} into {dest_path}')
        if type(file_path) == str:
            objs = [file_path]
        elif type(file_path) == list:
            objs = file_path
        try:
            for down_res in self.swift.download(container=container, objects=objs):
                if down_res['success']:
                    local_path = down_res['path']
                    shutil.move(local_path, dest_path)
                else:
                    logger.error("'%s' download failed" % down_res['object'])
        except SwiftError:
            logger.exception("error downloading file from SWIFT container")

    def get_swift_list(self, container, dir_name=None):
        """
        Return all contents of a given dir in SWIFT object storage.
        Goes through the pagination to obtain all file names.
        afaik, this is terribly inefficient, as we have to go through all the objects of the storage.
        """
        result = []
        try:
            list_parts_gen = self.swift.list(container=container)
            for page in list_parts_gen:
                if page["success"]:
                    for item in page["listing"]:
                        if dir_name is None or item["name"].startswith(dir_name):
                            result.append(item["name"])
                else:
                    logger.error(page["error"])
        except SwiftError as e:
            logger.error(e.value)
        return result
