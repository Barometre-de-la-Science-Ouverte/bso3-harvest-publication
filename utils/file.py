import os


def is_file_not_empty(filepath: str) -> bool:
    filesize = os.path.getsize(filepath)
    return filesize > 0


def write_to_file(file_content, filepath) -> None:
    with open(filepath, 'wb') as f:
        f.write(file_content)
