import json
from config.path_config import CONFIG_PATH, CONFIG_PATH_TEST

try:
    config_harvester = json.load(open(CONFIG_PATH, 'r'))
except FileNotFoundError:
    config_harvester = json.load(open(CONFIG_PATH_TEST, 'r'))

NB_SAMPLE_TO_HARVEST = config_harvester['nb_samples_to_harvest']
