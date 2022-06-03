import os
import gzip


def compress(file):
    deflated_file = file + ".gz"
    with open(file, "rb") as f_in:
        with gzip.open(deflated_file, "wb") as f_out:
            f_out.write(f_in.read())
    return deflated_file


def decompress(file):
    inflated_file = os.path.splitext(file)[0]
    with gzip.open(file, "rb") as f_in:
        with open(inflated_file, "wb") as f_out:
            f_out.write(f_in.read())
    return inflated_file
