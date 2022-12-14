class WileyClientMock:
    name = "wiley"

    def download_publication(self, doi: str, filepath: str) -> (str, str):
        return "fail", "wiley"


class ElsevierClientMock:
    name = "elsevier"

    def download_publication(self, doi: str, filepath: str) -> (str, str):
        return "fail", "elsevier"


wiley_client_mock = WileyClientMock()
elsevier_client_mock = ElsevierClientMock()
