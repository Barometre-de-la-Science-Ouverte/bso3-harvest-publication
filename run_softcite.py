from config.path_config import PUBLICATIONS_DOWNLOAD_DIR, CONFIG_PATH_SOFTCITE


def run_softcite(config_path, data_path, smc):
    client = smc(config_path)
    client.config["software_mention_url"] = f"http://{client.config['software_mention_host']}:{client.config['software_mention_port']}"
    client.annotate_directory(target="software", directory=data_path)


if __name__ == "__main__":
    from softdata_mentions_client.client import softdata_mentions_client

    # from tests.unit_tests.fixtures.software_mention_client import software_mentions_client as smc

    run_softcite(CONFIG_PATH_SOFTCITE, PUBLICATIONS_DOWNLOAD_DIR, softdata_mentions_client)
