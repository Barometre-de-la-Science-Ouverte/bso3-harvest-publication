class WileyClientMock:

    def download_publication(self, doi: str, filepath: str) -> (str, str):
        return 'fail', 'wiley'


wiley_client_mock = WileyClientMock()
