import os

PROJECT_DIRNAME = os.path.dirname(os.path.dirname(__file__))

# Metadata paths
DESTINATION_DIR_METADATA = os.path.join(PROJECT_DIRNAME, "tmp")
METADATA_LOCAL_FILE = "bso-publications-5k.jsonl.gz"  # "bso-publications-20220118.jsonl.gz" => Careful, implement a function to collect the last one on OVH

# Prefixes in ovh dump
METADATA_PREFIX = "metadata"
PUBLICATION_PREFIX = "publication"

DEFAULT_GROBID_TAG = "0.7.1-SNAPSHOT"
DEFAULT_SOFTCITE_TAG = "0.7.1-SNAPSHOT"

LOG_PATH = os.path.join(PROJECT_DIRNAME, os.path.join("logs", "logger.log"))

DATA_PATH = os.path.join(PROJECT_DIRNAME, "data")
PUBLICATIONS_DOWNLOAD_DIR = os.path.join(PROJECT_DIRNAME, "downloaded_publications/")

CONFIG_PATH = os.path.join(PROJECT_DIRNAME, "config.json")
CONFIG_DIR = os.path.join(PROJECT_DIRNAME, "static_config")
CONFIG_PATH_TEST = os.path.join(PROJECT_DIRNAME, "tests", "unit_tests", "config_test.json")
CONFIG_PATH_GROBID = os.path.join(CONFIG_DIR, "config_grobid.json")
CONFIG_PATH_SOFTCITE = os.path.join(CONFIG_DIR, "config_softcite.json")
CONFIG_PATH_OVH = os.path.join(CONFIG_DIR, "config.json")
CONFIG_SWIFT_PATH = os.path.join(CONFIG_DIR, "config_swift.json")
CONFIG_DB_PATH = os.path.join(CONFIG_DIR, "config_db.json")
CONFIG_APP_PATH = os.path.join(CONFIG_DIR, "config_app.json")
CONFIG_GROBID_PATH = os.path.join(CONFIG_DIR, "config_grobid.json")
CONFIG_SOFTCITE_PATH = os.path.join(CONFIG_DIR, "config_softcite.json")
