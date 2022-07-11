import os
from domain.processed_entry import ProcessedEntry
from domain.ovh_path import OvhPath
from harvester.OAHarvester import generateStoragePath
from config.processing_service_namespaces import grobid_ns, softcite_ns, datastet_ns

FIXTURES_PATH = os.path.dirname(__file__)

source_metadata_file = os.path.join(FIXTURES_PATH, 'bso-publications-5k.jsonl.gz')
filtered_metadata_filename = os.path.join(FIXTURES_PATH, 'filtered_' + os.path.basename(source_metadata_file))
doi_list = ['10.1111/jdv.15719']
expected_doi_filtered_content = [
    '{"affiliations": [{"detected_countries": ["de"], "name": "Department Dermatology and Allergy, Ludwig-Maximilian University, Munich, Germany."}, {"detected_countries": ["de"], "name": "M\\u00fcnchen Klinik Thalkirchner Stra\\u00dfe, Munich, Germany."}, {"detected_countries": ["pl"], "name": "Department of Dermatology, Venereology and Allergology, Wroclaw Medical University, Wroclaw, Poland."}, {"detected_countries": ["fr"], "name": "Department of Dermatology and Pediatric Dermatology, Hospital St. Andre, Bordeaux, France."}, {"detected_countries": ["de"], "name": "Department of Dermatology and Allergy Biederstein, Technische Universit\\u00e4t M\\u00fcnchen, Munich, Germany."}, {"detected_countries": ["ch"], "name": "Christine K\\u00fchne Center for Allergy Research and Education CK-CARE, Davos, Switzerland."}], "asjc_classification": [{"code_asjc": "2725", "field": "Infectious Diseases", "subject_area": "Health Sciences"}, {"code_asjc": "2708", "field": "Dermatology", "subject_area": "Health Sciences"}, {"code_asjc": "2725", "field": "Infectious Diseases", "subject_area": "Health Sciences"}, {"code_asjc": "2708", "field": "Dermatology", "subject_area": "Health Sciences"}], "bso_classification": "Medical research", "bsso_classification": {"field": ["Clinical Sciences"], "field_journal_title": ["Clinical Sciences"], "models": ["journal_title"], "weighted_score": 1.5}, "coi": null, "databank": [], "datasource": "pubmed_fr", "detected_countries": ["de", "fr", "ch", "pl"], "doi": "10.1111/jdv.15719", "domains": ["health"], "genre": "journal-article", "grants": null, "has_grant": false, "is_paratext": false, "issn_electronic": "1468-3083", "issn_list": ["0926-9959", "1468-3083"], "issn_print": null, "journal_issn_l": "0926-9959", "journal_issns": "0926-9959,1468-3083", "journal_name": "Journal of the European Academy of Dermatology and Venereology", "journal_title": "Journal of the European Academy of Dermatology and Venereology : JEADV", "keywords": [], "lang": "en", "mesh_headings": [], "pmid": 31259446, "publication_date": "2019-07-02T00:00:00", "publication_types": ["Published Erratum"], "publication_year": 2019, "published_date": "2019-07-01T00:00:00", "publisher": "Wiley", "sdg_classification": [{"sdg_code": "sdg3", "sdg_label": "3. Good health and well-being"}], "sources": ["pubmed"], "title": "Corrigendum: Consensus-based European guidelines for treatment of atopic eczema (atopic dermatitis) in adults and children: part I.", "url": "https://www.ncbi.nlm.nih.gov/pubmed/31259446", "year": 2019, "has_apc": true, "amount_apc_EUR": 2225.7061166538756, "apc_source": "openAPC_estimation_publisher_year", "amount_apc_openapc_EUR": 2225.7061166538756, "count_apc_openapc_key": 1303, "predatory_publisher": false, "predatory_journal": false, "publisher_normalized": "Wiley", "publisher_group": "Wiley", "publisher_dissemination": "Wiley", "genre_raw": "journal-article", "french_affiliations_types": ["hospital"], "author_useful_rank_fr": false, "author_useful_rank_countries": ["ch", "de"], "observation_dates": ["2021Q3", "2020", "2019"], "oa_details": {"2019": {"snapshot_date": "20191122", "observation_date": "2019", "is_oa": true, "journal_is_in_doaj": false, "journal_is_oa": false, "licence_publisher": ["no license"], "oa_locations": [{"url": "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719", "pmh_id": null, "is_best": true, "license": null, "updated": "2019-11-08T17:51:52.649712", "version": "publishedVersion", "evidence": "open (via free article)", "host_type": "publisher", "endpoint_id": null, "url_for_pdf": "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719", "url_for_landing_page": "https://doi.org/10.1111/jdv.15719", "repository_institution": null, "license_normalized": "no license"}], "oa_colors": ["hybrid"], "oa_colors_with_priority_to_publisher": ["hybrid"], "oa_host_type": "publisher"}, "2020": {"snapshot_date": "20201009", "observation_date": "2020", "is_oa": true, "journal_is_in_doaj": false, "journal_is_oa": false, "licence_publisher": ["no license"], "oa_locations": [{"url": "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719", "pmh_id": null, "is_best": true, "license": null, "oa_date": null, "updated": "2020-02-14T06:38:06.258581", "version": "publishedVersion", "evidence": "open (via free article)", "host_type": "publisher", "endpoint_id": null, "url_for_pdf": "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719", "url_for_landing_page": "https://doi.org/10.1111/jdv.15719", "repository_institution": null, "license_normalized": "no license"}], "oa_colors": ["hybrid"], "oa_colors_with_priority_to_publisher": ["hybrid"], "oa_host_type": "publisher"}, "2021Q3": {"snapshot_date": "20210901", "observation_date": "2021Q3", "is_oa": true, "journal_is_in_doaj": false, "journal_is_oa": false, "licence_publisher": ["no license"], "oa_locations": [{"url": "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719", "pmh_id": null, "is_best": true, "license": null, "oa_date": null, "updated": "2021-02-02T03:04:37.981717", "version": "publishedVersion", "evidence": "open (via free article)", "host_type": "publisher", "endpoint_id": null, "url_for_pdf": "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jdv.15719", "url_for_landing_page": "https://doi.org/10.1111/jdv.15719", "repository_institution": null, "license_normalized": "no license"}], "oa_colors": ["hybrid"], "oa_colors_with_priority_to_publisher": ["hybrid"], "oa_host_type": "publisher"}}, "amount_apc_doaj": null, "amount_apc_doaj_EUR": null, "has_coi": null}']


datastet_version_db: str = '0.7.2'
softcite_version_db: str = '0.7.2'
grobid_version_db: str = '0.7.2'
running_datastet_version: str = '0.7.2'
running_softcite_version: str = '0.7.2'
running_grobid_version: str = '0.7.2'
domain: str = 'arxiv'
url_used: str = 'http://arxiv.org/fake'
harvester_used = "standard"
rows_db: list = [
    ProcessedEntry(f"doi_{i}", f"uuid_{i}", "1", datastet_version_db, softcite_version_db, grobid_version_db, harvester_used, domain, url_used) for i in range(10)
]

high_spec_datastet_version: str = '0.7.5'
high_spec_softcite_version: str = '0.7.5'
high_spec_grobid_version: str = '0.7.5'
identical_spec_datastet_version: str = '0.7.2'
identical_spec_softcite_version: str = '0.7.2'
identical_spec_grobid_version: str = '0.7.2'
low_spec_datastet_version: str = '0.7.0'
low_spec_softcite_version: str = '0.7.0'
low_spec_grobid_version: str = '0.7.0'


uuid: str = 'a01b067e-d384-4387-8706-27b9b67927f'
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
    entry: ProcessedEntry = ProcessedEntry(f"doi_{i}", fuuid, "1", datastet_version_db, softcite_version_db, grobid_version_db, harvester_used, domain, url_used)
    file_path: OvhPath = f"{generateStoragePath(fuuid)}"

    publications_entries_datastet.append(entry)
    publications_entries_softcite.append(entry)
    publications_entries_grobid.append(entry)
    publication_files.append(f"{file_path}.extension")
    grobid_files_glob.append(f"{grobid_ns.dir}{file_path}.{grobid_ns.suffix}")
    softcite_files_glob.append(f"{softcite_ns.dir}{file_path}.{softcite_ns.suffix}")
    datastet_files_glob.append(f"{datastet_ns.dir}{file_path}.{datastet_ns.suffix}")

    expected_arg_update_database_processing_grobid.append((*entry, grobid_ns.service_name, running_grobid_version))
    expected_arg_update_database_processing_softcite.append((*entry, softcite_ns.service_name, running_softcite_version))
    expected_arg_update_database_processing_datastet.append((*entry, datastet_ns.service_name, running_datastet_version))
