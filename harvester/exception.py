class PublicationDownloadFileException(Exception):
    pass


class EmptyFileContentException(PublicationDownloadFileException):
    pass


class FailedRequest(PublicationDownloadFileException):
    pass
