import os
from config.path_config import PROJECT_DIRNAME

FLASK_APP = os.path.join(PROJECT_DIRNAME, 'application', 'run_harvester_app')
FLASK_ENV = 'dev'
FLASK_IP = '127.0.0.1'
FLASK_PORT = 8081
