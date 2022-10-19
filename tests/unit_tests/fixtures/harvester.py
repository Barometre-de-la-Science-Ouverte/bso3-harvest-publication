import json
import os

from config.harvester_config import get_harvester_config
from config.path_config import CONFIG_PATH_TEST, DATA_PATH
from harvester.OAHarvester import OAHarvester
from tests.unit_tests.fixtures.api_clients import wiley_client_mock, elsevier_client_mock
from tests.unit_tests.fixtures.harvester_constants import wiley_url

FIXTURES_PATH = os.path.dirname(__file__)


config_harvester = get_harvester_config(CONFIG_PATH_TEST)
harvester_2_publications = OAHarvester(config_harvester, wiley_client_mock, elsevier_client_mock)
harvester_2_publications_sample = OAHarvester(config_harvester, wiley_client_mock, elsevier_client_mock, sample=1)

sample_entries = [
    {
        "id": "8bd660e0-3a6c-4e1e-af55-f85df59c26a6",
        "doi": "10.1016/j.ijcard.2019.06.030",
        "domain": "Medical research",
        "oa_locations": [
            {
                "url": "https://hal.archives-ouvertes.fr/hal-02159827/file/2019%20gavotto%20etal.%2c%20factor%20associated%20with.pdf",
                "pmh_id": "oai:HAL:hal-02159827v1",
                "is_best": True,
                "license": None,
                "oa_date": None,
                "updated": "2021-08-07T19:46:58.684476",
                "version": "submittedVersion",
                "evidence": "oa repository (via OAI-PMH doi match)",
                "host_type": "repository",
                "endpoint_id": "b9bb6f966cfb6627303",
                "url_for_pdf": "https://hal.archives-ouvertes.fr/hal-02159827/file/2019%20Gavotto%20etal.%2C%20Factor%20associated%20with.pdf",
                "url_for_landing_page": "https://hal.archives-ouvertes.fr/hal-02159827/file/2019%20Gavotto%20etal.%2C%20Factor%20associated%20with.pdf",
                "repository_institution": "Aix Marseille UniversitÃ© - HAL AMU",
                "license_normalized": "no license",
                "repository_normalized": "HAL",
            },
            {
                "url": "https://hal.archives-ouvertes.fr/hal-02159827/document",
                "pmh_id": "oai:HAL:hal-02159827v1",
                "is_best": False,
                "license": None,
                "oa_date": None,
                "updated": "2021-03-12T09:22:50.557987",
                "version": "submittedVersion",
                "evidence": "oa repository (via OAI-PMH doi match)",
                "host_type": "repository",
                "endpoint_id": "0ad93bcc7d368da7e40",
                "url_for_pdf": "https://hal.archives-ouvertes.fr/hal-02159827/document",
                "url_for_landing_page": "https://hal.archives-ouvertes.fr/hal-02159827",
                "repository_institution": "Le Centre national de la recherche scientifique - HAL",
                "license_normalized": "no license",
                "repository_normalized": "HAL",
            },
        ],
    },
    {
        "id": "fb55ffd9-7188-4807-9b3f-e8fa647c9627",
        "doi": "10.1377/hlthaff.2018.05165",
        "domain": "Medical research",
        "oa_locations": [
            {
                "url": "http://europepmc.org/articles/pmc6690844?pdf=render",
                "pmh_id": "oai:europepmc.org:N4RTCr4p2TpW2odDVyTa",
                "is_best": True,
                "license": None,
                "oa_date": None,
                "updated": None,
                "version": "acceptedVersion",
                "evidence": "oa repository (via OAI-PMH doi match)",
                "host_type": "repository",
                "endpoint_id": "b5e840539009389b1a6",
                "url_for_pdf": "http://europepmc.org/articles/pmc6690844?pdf=render",
                "url_for_landing_page": "http://europepmc.org/articles/pmc6690844",
                "repository_institution": "PubMed Central - Europe PMC",
                "license_normalized": "no license",
                "repository_normalized": "PubMed Central",
            }
        ],
    },
]

sample_uuids = [entry["id"] for entry in sample_entries]

sample_urls_lists = []
for entry in sample_entries:
    sample_urls_lists.append(
        [oa_location["url_for_pdf"] for oa_location in entry["oa_locations"]]
    )

sample_filenames = [os.path.join(DATA_PATH, uuid + ".pdf") for uuid in sample_uuids]

pdf_file = os.path.join(FIXTURES_PATH, "original.pdf")
pdf_gz_file = os.path.join(FIXTURES_PATH, "original_gz.pdf.gz")

parsed_entry_filepath = os.path.join(FIXTURES_PATH, "oa_parsed_entry.json")
with open(parsed_entry_filepath, "rt") as fp:
    oa_entry_out = json.load(fp)

urls_entry = [
    "http://arxiv.org/pdf/1905.09044",
    "http://europepmc.org/articles/pmc6604379?pdf=render",
    "https://hal.archives-ouvertes.fr/hal-02298557/file/islandora_79998.pdf",
    "https://hal.archives-ouvertes.fr/hal-02298557/document",
    "https://univoak.eu/islandora/object/islandora%3A79998/datastream/PDF/view",
    wiley_url,
    "https://epigeneticsandchromatin.biomedcentral.com/track/pdf/10.1186/s13072-019-0285-6",
]

parsed_oa_entry_output = (urls_entry, oa_entry_out, sample_filenames[0])

parsed_ca_entry = (
    ["https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/ppl.13009"],
    {"id": sample_uuids[0], "doi": "10.1111/ppl.13009", "domain": "Biology (fond.)"},
    os.path.join(DATA_PATH, sample_uuids[0] + ".pdf"),
)

wiley_parsed_entry = (
    ["https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719"],
    {
        "id": sample_uuids[0],
        "doi": "10.1111/jdv.15719",
        "oa_locations": [
            {
                "url": "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719",
                "pmh_id": None,
                "is_best": True,
                "license": None,
                "oa_date": None,
                "updated": "2021-02-02T03:04:37.981717",
                "version": "publishedVersion",
                "evidence": "open (via free article)",
                "host_type": "publisher",
                "endpoint_id": None,
                "url_for_pdf": "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719",
                "url_for_landing_page": "https://doi.org/10.1111/jdv.15719",
                "repository_institution": None,
                "license_normalized": "no license",
            }
        ],
    },
    os.path.join(FIXTURES_PATH, sample_uuids[0] + ".pdf"),
)

arXiv_parsed_entry = (
    ["http://arxiv.org/pdf/1905.09044"],
    {
        "id": sample_uuids[0],
        "doi": "10.1111/jdv.15719",
        "oa_locations": [
            {
                "url": "http://arxiv.org/pdf/1905.09044",
                "pmh_id": "oai:arXiv.org:1905.09044",
                "is_best": True,
                "license": None,
                "oa_date": None,
                "updated": "2020-08-21T13:33:33.783240",
                "version": "submittedVersion",
                "evidence": "oa repository (via OAI-PMH doi match)",
                "host_type": "repository",
                "endpoint_id": "ca8f8d56758a80a4f86",
                "url_for_pdf": "http://arxiv.org/pdf/1905.09044",
                "url_for_landing_page": "http://arxiv.org/abs/1905.09044",
                "repository_institution": "Cornell University - arXiv",
                "license_normalized": "no license",
                "repository_normalized": "arXiv",
            }
        ],
    },
    os.path.join(FIXTURES_PATH, sample_uuids[0] + ".pdf"),
)

timeout_url = "http://jes.ecsdl.org/content/164/13/C717.full.pdf"
