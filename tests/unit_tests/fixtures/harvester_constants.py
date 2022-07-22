from config import CONFIG_WILEY_TOKEN_KEY, CONFIG_WILEY_EZPROXY_USER_KEY, CONFIG_WILEY_EZPROXY_PASS_KEY, \
    CONFIG_WILEY_PUBLICATION_URL_KEY, CONFIG_WILEY_BASE_URL_KEY

fake_doi = 'fake/doi'
fake_filepath = 'fake_file_path'
fake_file_content = '%PDF-fake_file_content'


# Wiley
wiley_fake_config = {
    CONFIG_WILEY_TOKEN_KEY: 'wiley_token',
    CONFIG_WILEY_EZPROXY_USER_KEY: 'wiley_ezproxy_user',
    CONFIG_WILEY_EZPROXY_PASS_KEY: 'wiley_ezproxy_pass',
    CONFIG_WILEY_PUBLICATION_URL_KEY: 'https://wiley-publication-url/',
    CONFIG_WILEY_BASE_URL_KEY: 'https://wiley-base-url.fr'
}

wiley_sleep_time_in_seconds_default = 1
wiley_doi = '10.1111/tpj.12099'
wiley_url = 'https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719'
