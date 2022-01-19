import logging.handlers
from config.path_config import LOG_PATH

time_handler = logging.handlers.TimedRotatingFileHandler(LOG_PATH, when='D', interval=1, backupCount=0)
time_handler.suffix = '%Y-%m-%d.log'
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
time_handler.setFormatter(formatter)
time_handler.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(time_handler)
