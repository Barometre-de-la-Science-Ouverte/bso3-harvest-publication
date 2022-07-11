from config.path_config import (CONFIG_PATH_GROBID, CONFIG_PATH_SOFTCITE,
                                CONFIG_PATH_DATASTET, DATASTET_DIR,
                                GROBID_DIR, SOFTCITE_DIR,
                                DATASTET_SUFFIX, DATASTET_PREFIX,
                                GROBID_SUFFIX, SOFTCITE_SUFFIX,
                                GROBID_PREFIX, SOFTCITE_PREFIX)
from types import SimpleNamespace

grobid_ns = SimpleNamespace()
grobid_ns.dir = GROBID_DIR
grobid_ns.suffix = GROBID_SUFFIX
grobid_ns.prefix = GROBID_PREFIX
grobid_ns.service_name = "grobid"
grobid_ns.config_path = CONFIG_PATH_GROBID

softcite_ns = SimpleNamespace()
softcite_ns.dir = SOFTCITE_DIR
softcite_ns.suffix = SOFTCITE_SUFFIX
softcite_ns.prefix = SOFTCITE_PREFIX
softcite_ns.service_name = "softcite"
softcite_ns.config_path = CONFIG_PATH_SOFTCITE

datastet_ns = SimpleNamespace()
datastet_ns.dir = DATASTET_DIR
datastet_ns.suffix = DATASTET_SUFFIX
datastet_ns.prefix = DATASTET_PREFIX
datastet_ns.service_name = "datastet"
datastet_ns.config_path = CONFIG_PATH_DATASTET
