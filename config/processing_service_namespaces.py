from config.path_config import (CONFIG_PATH_GROBID, CONFIG_PATH_SOFTCITE,
                                CONFIG_PATH_DATASTET, DATASTET_DIR,
                                GROBID_DIR, SOFTCITE_DIR,
                                DATASTET_SUFFIX, DATASTET_PREFIX,
                                GROBID_SUFFIX, SOFTCITE_SUFFIX,
                                GROBID_PREFIX, SOFTCITE_PREFIX)
from types import SimpleNamespace

class ServiceNamespace(SimpleNamespace):
    def __init__(self, _dir, suffix, prefix, service_name, config_path) -> None:
        self.dir: str = _dir
        self.suffix: str = suffix
        self.prefix: str = prefix
        self.service_name: str = service_name
        self.config_path: str = config_path

grobid_ns = ServiceNamespace(GROBID_DIR, GROBID_SUFFIX, GROBID_PREFIX, "grobid", CONFIG_PATH_GROBID)
softcite_ns = ServiceNamespace(SOFTCITE_DIR, SOFTCITE_SUFFIX, SOFTCITE_PREFIX, "softcite", CONFIG_PATH_SOFTCITE)
datastet_ns = ServiceNamespace(DATASTET_DIR, DATASTET_SUFFIX, DATASTET_PREFIX, "datastet", CONFIG_PATH_DATASTET)
