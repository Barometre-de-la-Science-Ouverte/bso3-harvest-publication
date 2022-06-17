Feature: Harvesting

    Scenario: harvesting for Arxiv
        Given a set of specific doi
            | doi                        |
            | 10.1038/s41467-018-07180-3 | 
            | 10.1038/s41467-018-07491-5 | 
            | 10.1073/pnas.1809642115    |
        and a db_handler to postgres database for "harvested_status_table" table
        When we send a post request with metadata_file="bso-publications-5k.jsonl.gz" to "http://127.0.0.1:5004/harvest_partitions" endpoint
        and we wait "90" seconds
        Then we check that the doi are present in postgres database
        and we check that all uid of doi downloaded from postgres database on the table are present in their metadata + publication form on swift
    
    Scenario: harvesting for Standard
        Given a set of specific doi
            | doi                             |
            | 10.1001/jamainternmed.2019.1047 |
            | 10.1007/978-1-4939-9074-0_11    |
            | 10.1007/s00520-019-04890-2      |
        and a db_handler to postgres database for "harvested_status_table" table
        When we send a post request with metadata_file="bso-publications-5k.jsonl.gz" to "http://127.0.0.1:5004/harvest_partitions" endpoint
        and we wait "90" seconds
        Then we check that the doi are present in postgres database
        and we check that all uid of doi downloaded from postgres database on the table are present in their metadata + publication form on swift

    Scenario: harvesting for Wiley
        Given a set of specific doi
            | doi                   |
            | 10.1002/ijc.32590     |
            | 10.1096/fj.201900895r |
            | 10.1111/bjh.16083     |
        and a db_handler to postgres database for "harvested_status_table" table
        When we send a post request with metadata_file="bso-publications-5k.jsonl.gz" to "http://127.0.0.1:5004/harvest_partitions" endpoint
        and we wait "90" seconds
        Then we check that the doi are present in postgres database
        and we check that all uid of doi downloaded from postgres database on the table are present in their metadata + publication form on swift