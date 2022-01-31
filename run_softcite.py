import os
import sys
from config.path_config import PUBLICATIONS_DOWNLOAD_DIR, CONFIG_PATH_SOFTCITE


def run_softcite(config_path, data_path, smc):
    client = smc(config_path)
    client.annotate_directory(data_path)
    client.diagnostic(full_diagnostic=False)


if __name__ == "__main__":
    from software_mentions_client.client import software_mentions_client as smc

    run_softcite(CONFIG_PATH_SOFTCITE, PUBLICATIONS_DOWNLOAD_DIR, smc)

