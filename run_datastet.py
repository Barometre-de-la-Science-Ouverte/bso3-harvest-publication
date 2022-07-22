from config.path_config import CONFIG_PATH_DATASTET, PUBLICATIONS_DOWNLOAD_DIR


def run_datastet(config_path, data_path, softdata_mentions_client):
    client = softdata_mentions_client(config_path=config_path)
    client.config["dataset_mention_url"] = f"http://{client.config['dataset_mention_host']}:{client.config['dataset_mention_port']}"
    client.annotate_directory(target="dataset", directory=data_path)



if __name__ == "__main__":
    from softdata_mentions_client.client import softdata_mentions_client
    run_datastet(CONFIG_PATH_DATASTET, PUBLICATIONS_DOWNLOAD_DIR, softdata_mentions_client)

