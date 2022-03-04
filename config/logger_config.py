import logging

from config.harvester_config import config_harvester

is_debug_level = config_harvester['is_level_debug']
print("is_debug_level", is_debug_level)
if is_debug_level == 1:
    LOGGER_LEVEL = logging.DEBUG
else:
    LOGGER_LEVEL = logging.WARNING
print("logger should be set to", LOGGER_LEVEL)