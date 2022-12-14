import os
from datetime import datetime

from domain.processed_entry import ProcessedEntry
from domain.ovh_path import OvhPath
from harvester.OAHarvester import generateStoragePath
from config.processing_service_namespaces import grobid_ns, softcite_ns, datastet_ns

FIXTURES_PATH = os.path.dirname(__file__)

source_metadata_file = os.path.join(FIXTURES_PATH, "bso-publications-10.jsonl.gz")
filtered_metadata_filename = os.path.join(
    FIXTURES_PATH, "filtered_" + os.path.basename(source_metadata_file)
)
doi_list = ["10.1158/1538-7445.sabcs21-p1-17-07"]
expected_doi_filtered_content = [
    '{"affiliations": [{"detected_countries": ["fr"]}, {"detected_countries": ["fr"]}, {"detected_countries": ["fr"]}], "all_ids": ["doi10.1158/1538-7445.sabcs21-p1-17-07"], "bso_classification": "Medical research", "bso_country": ["fr"], "datasource": "crossref_fr", "detected_countries": ["fr"], "doi": "10.1158/1538-7445.sabcs21-p1-17-07", "external_ids": [{"crossref": "10.1158/1538-7445.sabcs21-p1-17-07"}], "genre": "journal-article", "genre_raw": "journal-article", "id": "doi10.1158/1538-7445.sabcs21-p1-17-07", "id_type": "doi", "is_paratext": false, "journal_issn_l": "0008-5472", "journal_issns": "0008-5472,1538-7445", "journal_name": "Cancer Research", "natural_id": null, "published_date": "2022-02-15T00:00:00", "publisher": "American Association for Cancer Research (AACR)", "publisher_dissemination": "American Association for Cancer Research", "publisher_group": "American Association for Cancer Research", "publisher_normalized": "American Association for Cancer Research", "sources": ["json"], "title": "Abstract P1-17-07: Consequences of stopping a 4/6 cyclin D-dependent kinase Inhibitor in metastatic breast cancer patients with clinical benefit on endocrine treatment, in the context of the COVID-19 outbreak", "url": "http://doi.org/10.1158/1538-7445.sabcs21-p1-17-07", "year": 2022, "has_apc": false, "lang": "en", "publisher_in_bealls_list": false, "journal_or_publisher_in_bealls_list": false, "observation_dates": ["2022Q3"], "oa_details": {"2022Q3": {"snapshot_date": "20220823", "observation_date": "2022Q3", "is_oa": false, "journal_is_in_doaj": false, "journal_is_oa": false, "oa_host_type": ["closed"], "oa_colors": ["closed"], "oa_colors_with_priority_to_publisher": ["closed"]}}, "amount_apc_doaj": null, "amount_apc_doaj_EUR": null, "amount_apc_EUR": null, "has_coi": null, "has_grant": null, "pmid": null, "publication_year": null, "french_affiliations_types": ["hospital"], "author_useful_rank_fr": false, "author_useful_rank_countries": []}'
]

datastet_version_db: str = "0.7.2"
softcite_version_db: str = "0.7.2"
grobid_version_db: str = "0.7.2"
running_datastet_version: str = "0.7.2"
running_softcite_version: str = "0.7.2"
running_grobid_version: str = "0.7.2"
harvesting_date = datetime(2022, 6, 24, 19, 0, 0)
domain: str = "arxiv"
url_used: str = "http://arxiv.org/fake"
harvester_used = "standard"
rows_db: list = [
    ProcessedEntry( f"doi_{i}", f"uuid_{i}", "1",
        softcite_version_db, grobid_version_db,
        harvester_used, domain, url_used, harvesting_date,
        datastet_version_db,
    ) for i in range(10)
]
entries_to_process = [ProcessedEntry(
    "doi", "8bd660e0-3a6c-4e1e-af55-f85df59c26a6", "1",
    softcite_version_db, grobid_version_db,
    harvester_used, domain, url_used, harvesting_date,
    datastet_version_db,
)]
expected_files_to_process = [
    'publication/8b/d6/60/e0/8bd660e0-3a6c-4e1e-af55-f85df59c26a6/8bd660e0-3a6c-4e1e-af55-f85df59c26a6.pdf.gz'
]

expected_partitions = [
    [
        'publication/uu/id/_0//uuid_0/uuid_0.pdf.gz',
        'publication/uu/id/_1//uuid_1/uuid_1.pdf.gz',
    ],[
        'publication/uu/id/_2//uuid_2/uuid_2.pdf.gz',
        'publication/uu/id/_3//uuid_3/uuid_3.pdf.gz',
    ],[
        'publication/uu/id/_4//uuid_4/uuid_4.pdf.gz',
        'publication/uu/id/_5//uuid_5/uuid_5.pdf.gz',
    ],[
        'publication/uu/id/_6//uuid_6/uuid_6.pdf.gz',
        'publication/uu/id/_7//uuid_7/uuid_7.pdf.gz',
    ],[
        'publication/uu/id/_8//uuid_8/uuid_8.pdf.gz',
        'publication/uu/id/_9//uuid_9/uuid_9.pdf.gz',
    ]
]

high_spec_datastet_version: str = "0.7.5"
high_spec_softcite_version: str = "0.7.5"
high_spec_grobid_version: str = "0.7.5"
identical_spec_datastet_version: str = "0.7.2"
identical_spec_softcite_version: str = "0.7.2"
identical_spec_grobid_version: str = "0.7.2"
low_spec_datastet_version: str = "0.7.0"
low_spec_softcite_version: str = "0.7.0"
low_spec_grobid_version: str = "0.7.0"

uuid: str = "a01b067e-d384-4387-8706-27b9b67927f"
publications_entries_datastet: list = []
publications_entries_softcite: list = []
publications_entries_grobid: list = []
publication_files: list = []
grobid_files_glob: list = []
softcite_files_glob: list = []
datastet_files_glob: list = []

expected_arg_update_database_processing_grobid: list = []
expected_arg_update_database_processing_softcite: list = []
expected_arg_update_database_processing_datastet: list = []

for i in range(3):
    fuuid: str = f"uuid_{i}"
    entry: ProcessedEntry = ProcessedEntry(
        f"doi_{i}",
        fuuid,
        "1",
        softcite_version_db,
        grobid_version_db,
        harvester_used,
        domain,
        url_used,
        harvesting_date,
        datastet_version_db,
    )
    file_path: OvhPath = f"{generateStoragePath(fuuid)}"

    publications_entries_datastet.append(entry)
    publications_entries_softcite.append(entry)
    publications_entries_grobid.append(entry)
    publication_files.append(f"{file_path}.extension")
    grobid_files_glob.append(f"{grobid_ns.dir}{file_path}.{grobid_ns.suffix}")
    softcite_files_glob.append(f"{softcite_ns.dir}{file_path}.{softcite_ns.suffix}")
    datastet_files_glob.append(f"{datastet_ns.dir}{file_path}.{datastet_ns.suffix}")

    expected_arg_update_database_processing_grobid.append(
        (*entry, grobid_ns.service_name, running_grobid_version)
    )
    expected_arg_update_database_processing_softcite.append(
        (*entry, softcite_ns.service_name, running_softcite_version)
    )
    expected_arg_update_database_processing_datastet.append(
        (*entry, datastet_ns.service_name, running_datastet_version)
    )
