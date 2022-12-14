from behave import given, when, then
from time import sleep
from requests import post
from json import dumps
from ovh_handler import generateStoragePath
from infrastructure.database.db_handler import DBHandler
from config.harvester_config import config_harvester
from infrastructure.storage.swift import Swift
from tests.e2e_tests.db_connection import DBConnection
from config.path_config import COMPRESSION_EXT, METADATA_EXT, PUBLICATION_PREFIX, METADATA_PREFIX, PUBLICATION_EXT
from domain.ovh_path import OvhPath


@given('a clean database without rows')
def clean_database(context):
    context.db_handler.engine.execute(f'DELETE FROM {context.db_handler.table_name};')

    assert context.db_handler.count() == 0


@given('a set of specific doi')
def set_specific_doi(context):
    context.doi_list = []
    for row in context.table:
        context.doi_list.append(row['doi'])


@given('a db_handler to postgres database for "{table}" table')
def set_db_handler(context, table):
    swift_handler: Swift = Swift(config_harvester)
    config: dict = {
        'db_host': 'localhost',
        'db_user': config_harvester["db"]["db_user"],
        'db_port': config_harvester["db"]["db_port"],
        'db_name': config_harvester["db"]["db_name"],
        'db_password': config_harvester["db"]["db_password"],
        }
    connection: DBConnection = DBConnection(config)
    db_handler: DBHandler = DBHandler(engine=connection.engine, table_name=table, swift_handler=swift_handler)

    context.db_handler = db_handler


@when('we send a post request with metadata_file="{metadata_file}", total_partition_number="{total_partition_number}" to "{url}" endpoint')
def post_request(context, metadata_file, total_partition_number, url):
    headers: str = "Content-Type: application/json"
    total_partition_number: int = int(total_partition_number)
    doi_list: str = dumps(context.doi_list)
    obj: dict = {
        "metadata_file": metadata_file,
        "total_partition_number": total_partition_number,
        "doi_list": doi_list
        }
    obj: str = dumps(obj)
    context.res = post(url, obj, headers)
    context.total_partition_number = total_partition_number


@when('we wait "{number}" seconds')
def wait_by_time(context, number):
    sleep(int(number))


@then('we check that the response status is "{status_code_expected}"')
def check_response_status_code(context, status_code_expected):
    status_code: int = context.res.status_code

    assert status_code == int(status_code_expected)


@then('we check that the response content length is equals to total_partition_number + 1')
def check_response_json_length(context):
    length_response: int = len(context.res.json())
    length_expected: int = context.total_partition_number + 1

    assert length_response == length_expected


@then('we check that the number of rows in database is equals to the number of inputs')
def check_number_rows_request_count_postgres(context):
    number_rows_request: int = context.db_handler.count()
    number_rows_expected: int = len(context.doi_list)

    assert number_rows_request == number_rows_expected


@then('we check that the doi are present in postgres database')
def check_doi_in_postgres(context):
    postgres_result: list = context.db_handler.fetch_all()

    size_doi = len(context.doi_list)

    counter = 0

    for row in postgres_result:
        for doi in context.doi_list:
            if row[0] == doi:
                counter += 1

    assert counter == size_doi


@then('we check that all uid of doi downloaded from postgres database on the table are present in their metadata + publication form on swift')
def check_uuid_from_postgres_to_swift(context):
    swift_list: list = context.db_handler.swift_handler.get_swift_list(container=config_harvester['publications_dump'])

    extension_metadata: str = METADATA_EXT + COMPRESSION_EXT
    extension_publication: str = PUBLICATION_EXT + COMPRESSION_EXT

    postgres_result_list: list = context.db_handler.fetch_all()
    postgres_metadata_list: list = []
    postgres_publications_list: list = []

    for row in postgres_result_list:
        uuid: str = row[1]
        storage_path: str = generateStoragePath(uuid)
        postgres_metadata_list.append(str(OvhPath(METADATA_PREFIX, storage_path, uuid + extension_metadata)))
        postgres_publications_list.append(str(OvhPath(PUBLICATION_PREFIX, storage_path, uuid + extension_publication)))

    size_result_expected: int = len(postgres_result_list)

    n_metadata: int = 0
    n_publications: int = 0
    can_pass: bool = False

    for name in swift_list:
        for name_metadata in postgres_metadata_list:
            if name == name_metadata:
                n_metadata += 1
                can_pass = True
                break
        if not can_pass:
            for name_publications in postgres_publications_list:
                if name == name_publications:
                    n_publications += 1
                    break
        can_pass = False

    assert n_metadata == size_result_expected
    assert n_publications == size_result_expected
