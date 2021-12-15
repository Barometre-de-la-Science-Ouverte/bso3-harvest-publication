import json
import os

from harvester.OAHarvester import OAHarvester
from config.path_config import DATA_PATH, CONFIG_PATH

FIXTURES_PATH = os.path.dirname(__file__)

config_harvester = json.load(open(CONFIG_PATH, 'r'))
harvester_2_publications = OAHarvester(config_harvester, thumbnail=False, sample=2)

urls_2_publications = [
    'https://hal.archives-ouvertes.fr/hal-02159827/file/2019%20Gavotto%20etal.%2C%20Factor%20associated%20with.pdf',
    'http://europepmc.org/articles/pmc6690844?pdf=render']

filename_2_publications = [
    os.path.join(DATA_PATH, '8bd660e0-3a6c-4e1e-af55-f85df59c26a6.pdf'),
    os.path.join(DATA_PATH, 'fb55ffd9-7188-4807-9b3f-e8fa647c9627.pdf')]

entries_2_publications = [
    {'id': '8bd660e0-3a6c-4e1e-af55-f85df59c26a6',
     'url': 'https://hal.archives-ouvertes.fr/hal-02159827/file/2019%20gavotto%20etal.%2c%20factor%20associated%20with.pdf',
     'pmh_id': 'oai:HAL:hal-02159827v1', 'is_best': True, 'license': None, 'oa_date': None,
     'updated': '2021-08-07T19:46:58.684476', 'version': 'submittedVersion',
     'evidence': 'oa repository (via OAI-PMH doi match)', 'host_type': 'repository',
     'endpoint_id': 'b9bb6f966cfb6627303',
     'url_for_pdf': 'https://hal.archives-ouvertes.fr/hal-02159827/file/2019%20Gavotto%20etal.%2C%20Factor%20associated%20with.pdf',
     'url_for_landing_page': 'https://hal.archives-ouvertes.fr/hal-02159827/file/2019%20Gavotto%20etal.%2C%20Factor%20associated%20with.pdf',
     'repository_institution': 'Aix Marseille UniversitÃ© - HAL AMU', 'license_normalized': 'no license',
     'repository_normalized': 'HAL'},
    {'id': 'fb55ffd9-7188-4807-9b3f-e8fa647c9627', 'url': 'http://europepmc.org/articles/pmc6690844?pdf=render',
     'pmh_id': 'oai:europepmc.org:N4RTCr4p2TpW2odDVyTa', 'is_best': True, 'license': None, 'oa_date': None,
     'updated': None, 'version': 'acceptedVersion', 'evidence': 'oa repository (via OAI-PMH doi match)',
     'host_type': 'repository', 'endpoint_id': 'b5e840539009389b1a6',
     'url_for_pdf': 'http://europepmc.org/articles/pmc6690844?pdf=render',
     'url_for_landing_page': 'http://europepmc.org/articles/pmc6690844',
     'repository_institution': 'PubMed Central - Europe PMC', 'license_normalized': 'no license',
     'repository_normalized': 'PubMed Central'}
]

ids_2_publications = ['8bd660e0-3a6c-4e1e-af55-f85df59c26a6', 'fb55ffd9-7188-4807-9b3f-e8fa647c9627']