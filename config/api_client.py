from config import WILEY_KEY
from config.harvester_config import config_harvester
from harvester.wiley_client import WileyClient

wiley_client = WileyClient(config_harvester[WILEY_KEY], sleep_time_in_seconds=1)
