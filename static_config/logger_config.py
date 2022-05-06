import logging

from static_config.config_generator import config_json

is_debug_level = config_json["is_level_debug"]
if is_debug_level == 1:
    LOGGER_LEVEL = logging.DEBUG
else:
    LOGGER_LEVEL = logging.WARNING
