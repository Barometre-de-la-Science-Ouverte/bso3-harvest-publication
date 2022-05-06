import json
import os

from dotenv import load_dotenv

from static_config.path_config import CONFIG_PATH, CONFIG_SWIFT_PATH, CONFIG_DB_PATH, CONFIG_APP_PATH, \
    CONFIG_GROBID_PATH, CONFIG_SOFTCITE_PATH

config_json = json.load(open(CONFIG_PATH, "r"))
config_swift_json = json.load(open(CONFIG_SWIFT_PATH, "r"))
config_db_json = json.load(open(CONFIG_DB_PATH, "r"))
config_app_json = json.load(open(CONFIG_APP_PATH, "r"))
config_grobid = json.load(open(CONFIG_GROBID_PATH, "r"))
config_softcite = json.load(open(CONFIG_SOFTCITE_PATH, "r"))

try:
    load_dotenv()
except Exception:
    print("File .env not found")

# Add env var secrets & pwd for swift - ovh
config_json["swift"] = config_swift_json
config_json["swift"]["OS_USERNAME"] = os.getenv("OS_USERNAME")
config_json["swift"]["OS_PASSWORD"] = os.getenv("OS_PASSWORD")
config_json["swift"]["OS_PROJECT_ID"] = os.getenv("OS_PROJECT_ID")
config_json["swift"]["swift_container"] = config_json["publications_dump"]

# Database Postgres variables
config_json["db"] = config_db_json
config_json["db"]["DB_PASSWORD"] = os.getenv("DB_PASSWORD")

# flask app config file
config_json["app"] = config_app_json

# Add env var token for harvest request
config_json["token"] = {}
config_json["token"]["WILEY"] = os.getenv("TOKEN_WILEY")
config_json["token"]["ELSEVIER"] = os.getenv("TOKEN_ELSEVIER")
config_json["token"]["SPRINGER"] = os.getenv("TOKEN_SPRINGER")

# Add grobid
config_json["grobid"] = config_grobid

# Add softcite
config_json["softcite"] = config_softcite
