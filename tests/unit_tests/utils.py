from tests.unit_tests.fixtures.harvester_constants import fake_file_content


class ResponseMock:

    def __init__(self, status_code, content=fake_file_content):
        self.status_code = status_code
        self.ok = True if status_code == 200 else False
        self.content = content
