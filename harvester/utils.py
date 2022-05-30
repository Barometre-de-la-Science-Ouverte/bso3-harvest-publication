import os


def is_file_not_empty(filepath: str) -> bool:
    filesize = os.path.getsize(filepath)
    return filesize > 0
