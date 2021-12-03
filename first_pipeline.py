import argparse
import importlib
import json
import os
import sys
import time
import requests

# sys path hack pour pouvoir importer les modules dont j'ai besoin
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from software_mentions_client import software_mention_client as smc

OAHarvester = importlib.import_module('biblio-glutton-harvester.OAHarvester')
from grobid_client.grobid_client import GrobidClient


def harvest_10_pmc(config, pmc_path):
    harvester = OAHarvester.OAHarverster(config, thumbnail=False, sample=10)
    harvester.harvestPMC(pmc_path)
    harvester.diagnostic()


def run_softcite(config_path, data_path):
    # Ne s'execute pas sur des pdfs compressés (.gz) -> config_harvester compression: false
    client = smc.software_mention_client(config_path)
    client.annotate_collection(data_path)
    client.diagnostic(full_diagnostic=False)


def run_grobid(config_path, data_path):
    client = GrobidClient(config_path=config_path)
    client.process("processFulltextDocument", data_path, output=f"{data_path}/grobid_out/", consolidate_citations=True, tei_coordinates=True, force=True, verbose=True, n=4)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Download 10 randomly selected PDFs from pmc and run software mention detection on them. Require software_mentions to run on http://localhost:8060")
    parser.add_argument("--no-harvest", action="store_true", help="run software mention detection data already downloaded")
    args = parser.parse_args()
    do_harvest = not args.no_harvest

    grobid_up = requests.get("http://localhost:8070").status_code == 200
    softcite_up = requests.get("http://localhost:8060").status_code == 200

    while not (grobid_up and softcite_up):
        print("Waiting 5s while services start")
        time.sleep(5)

    config_harvester = json.load(open('config_harvester.json','r'))
    pmc_path = '../oa_file_list.txt'
    config_path_softcite = 'config_softcite.json'
    config_path_grobid = 'config_grobid.json'
    
    start_time = time.time()
    if do_harvest:
        harvest_10_pmc(config_harvester, pmc_path)
        runtime = round(time.time() - start_time, 3)
        print(f"harvest duration: {runtime}s")
    
    run_softcite(config_path_softcite, config_harvester['data_path'])
    runtime1 = round(time.time() - runtime, 3)
    print(f"softcite step duration: {runtime1}s")
    
    run_grobid(config_path_grobid, config_harvester['data_path'])
    runtime2 = round(time.time() - runtime1, 3)
    print(f"grobid step duration: {runtime2}s")
    total_duration = round(time.time() - start_time, 3)
    print(f"total duration: {total_duration}s")

    # TODO Find out why containers crash (mainly softcite)
    # TODO Find out why grobid 408 on some pdf
    # TODO parallize grobid & softcite
    # TODO Index what is already processed
