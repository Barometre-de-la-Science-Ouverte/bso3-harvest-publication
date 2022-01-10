import os
from config.path_config import PROJECT_DIRNAME
from application.server.views import app

app_path = os.path.join(PROJECT_DIRNAME, 'application', 'run_harvester_app')

# Set flask app environment variables
os.environ['FLASK_APP'] = app_path
os.environ['FLASK_ENV'] = 'dev'

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=True)