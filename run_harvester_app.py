import os

from application.server.views import app
from config.app_config import FLASK_APP, FLASK_ENV, FLASK_IP, FLASK_PORT

os.environ['FLASK_APP'] = FLASK_APP
os.environ['FLASK_ENV'] = FLASK_ENV

if __name__ == "__main__":
    app.run(host=FLASK_IP, port=FLASK_PORT, debug=True)
