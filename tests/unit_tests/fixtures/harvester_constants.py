from config import WILEY_TOKEN_KEY, WILEY_PUBLICATION_URL_KEY

fake_doi = 'fake/doi'
fake_filepath = 'fake_file_path'
fake_file_content = '%PDF-fake_file_content'


# Wiley
wiley_fake_config = {
    "name": "WILEY",
    "HEADERS": {
        'Accept': 'application/pdf',
        "Wiley-TDM-Client-Token": "wiley_token"
    },
    "PUBLICATION_URL": "https://wiley-publication-url/",
    "health_check_doi": "wiley_health_check_doi",
    "throttle_parameters": {
        "max_num_requests": 1,
        "window_size": 1
    }
}
# Elsevier config
elsevier_fake_config = {
    "name": "ELSEVIER",
    "HEADERS": {
        'Accept': 'application/pdf',
        'X-ELS-APIKey': "elsevier_api_token",
        'X-ELS-Insttoken': "elsevier_inst_token"
    },
    "PUBLICATION_URL": "https://elsevier-publication-url/",
    "health_check_doi": "elsevier_health_check_doi",
    "throttle_parameters": {
        "max_num_requests": 1,
        "window_size": 1
    }
}


wiley_sleep_time_in_seconds_default = 1
wiley_doi = '10.1111/tpj.12099'
wiley_url = 'https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719'
