import os
from config.storage_config import PUBLICATIONS_DUMP

from swiftclient.service import SwiftError, SwiftService, SwiftUploadObject

from logger import logger


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
                        if i_name == PUBLICATIONS_DUMP:
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
        print(self.config["swift"])
        for key in self.config["swift"]:
            if len(self.config["swift"][key].strip()) > 0:
                options[key] = self.config["swift"][key]
        return options

    def upload_files_to_swift(self, container, file_paths, dest_path=None):
        """
        Bulk upload of a list of files to current SWIFT object storage container under the same destination path
        """
        objs = []

        # file object
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            object_name = file_name
            if dest_path is not None:
                object_name = dest_path + "/" + file_name

            obj = SwiftUploadObject(file_path, object_name=object_name)
            objs.append(obj)

        try:
            for result in self.swift.upload(container, objs):
                print(result)
                if not result['success']:
                    error = result['error']
                    if result['action'] == "upload_object":
                        logger.error("Failed to upload object %s to container %s: %s" % (
                            container, result['object'], error))
                    else:
                        logger.error("%s" % error)
        except SwiftError:
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
