import json
from config.path_config import CONFIG_PATH

config_harvester = json.load(open(CONFIG_PATH, 'r'))
NB_SAMPLE_TO_HARVEST = config_harvester['nb_samples_to_harvest']
