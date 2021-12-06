import os

PROJECT_DIRNAME = os.path.dirname(os.path.dirname(__file__))
HARVESTER_CONFIG_PATH = os.path.join(PROJECT_DIRNAME, 'config.json')
PMC_PATH = os.path.join(os.path.dirname(PROJECT_DIRNAME), 'oa_file_list.txt')
