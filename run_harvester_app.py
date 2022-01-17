import os

from application.server.views import app
from config.harvester_config import config_harvester
from config.path_config import PROJECT_DIRNAME

FLASK_APP = os.path.join(PROJECT_DIRNAME, 'run_harvester_app')
FLASK_ENV = config_harvester['app']['flask_env']
FLASK_IP = config_harvester['app']['flask_ip']
FLASK_PORT = config_harvester['app']['flask_port']

os.environ['FLASK_APP'] = FLASK_APP
os.environ['FLASK_ENV'] = FLASK_ENV

if __name__ == "__main__":
    app.run(host=FLASK_IP, port=FLASK_PORT, debug=True)
