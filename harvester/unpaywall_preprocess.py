"""

A small preprocessing script for unpaywall dump file. The idea is to create partitions
to distribute the processing if required and avoid repeating too many queries on the same 
domains. 

What is done by the script:
- skip entries without PDF open access resource
- distribute the entries with open access resource in n bins/files

"""

import argparse
import gzip
import json
import os
import time

from tqdm import tqdm
from harvester.OAHarvester import _count_entries, get_nth_key


def create_partition(unpaywall, output=None, nb_bins=10, keep=True) -> None:
    """Filter the archive file and split it into nb_bins (compressed) files"""
    if (output and os.path.isdir(output) and len(os.listdir(output)) > 0) or len(os.listdir(os.path.dirname(unpaywall))) > 1:
        print("Partitions probably exist already")
        return
    count = _count_entries(gzip.open, unpaywall)
    nb_oa_entries = 0
    # prepare the n bins files
    nbins_files = []
    basename = os.path.basename(unpaywall).rstrip('.jsonl.gz')

    for n in range(nb_bins):
        if output is None:
            dirname = os.path.dirname(unpaywall)
            out_path = os.path.join(dirname, basename + "_" + str(n) + ".jsonl.gz")
        else:
            if not os.path.isdir(output):
                os.makedirs(output)
            out_path = os.path.join(output, basename + "_" + str(n) + ".jsonl.gz")
        f = gzip.open(out_path, 'wt')
        nbins_files.append(f)

    with gzip.open(unpaywall, 'rt') as gz:
        current_bin = 0
        for position, line in enumerate(tqdm(gz, total=count)):
            entry = json.loads(line)
            latest_observation = entry['oa_details'][get_nth_key(entry['oa_details'], -1)]
            if latest_observation['is_oa']:
                for oa_location in latest_observation['oa_locations']:
                    if oa_location['is_best'] and oa_location['url_for_pdf']:
                        nbins_files[current_bin].write(line)
                        current_bin = (current_bin + 1) % nb_bins
                        nb_oa_entries += 1

    for n in range(nb_bins):
        nbins_files[n].close()

    print(str(nb_bins), "files generated, with a total of", str(nb_oa_entries), "OA entries with PDF URL")

    if not keep:
        os.remove(unpaywall)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open Access PDF harvester")
    parser.add_argument("--unpaywall", default=None, help="path to the Unpaywall dataset (gzipped)")
    parser.add_argument("--output",
                        help="where to write the pre-processed files (default along with the Unpaywall input file)")
    parser.add_argument("--n", type=int, default="10", help="number of bins for partitioning the unpaywall entries")

    args = parser.parse_args()

    unpaywall = args.unpaywall
    output = args.output
    nb_bins = args.n

    if unpaywall is None:
        print("error: the path to the Unpaywall file has not been specified")
    elif not os.path.isfile(unpaywall):
        print("error: the indicated path to the Unpaywall file is not valid", unpaywall)
    elif output is not None and not os.path.isdir(output):
        print("error: the indicated output path is not valid", output)
    else:
        start_time = time.time()

        create_partition(unpaywall, output, nb_bins)

        runtime = round(time.time() - start_time, 3)
        print("runtime: %s seconds " % runtime)
