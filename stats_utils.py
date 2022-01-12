import csv
import json
import os
import pickle
from datetime import date, datetime

import lmdb
import pandas as pd

DATA_PATH = './data'


def extract_stats_from_logs(log_filepath):
    with open(log_filepath, "r") as f:
        return [json.loads(line.lstrip('INFO:root:').rstrip('\n'))['Stats'] for line in f.readlines() if line.startswith('INFO:root:{"Stats"')]

def write_jsonl(data, filepath):
    with open(filepath, "w") as f:
        for line in data:
            f.write(json.dumps(line) + '\n')

def read_stats_file(file_path):
    with open(file_path, "r") as f:
        return [json.loads(line) for line in f.readlines()]

def summary(stats):
    nb_harvested = sum([int(stat['is_harvested']) for stat in stats])
    nb_total = sum([1 for stat in stats])
    print(f"{nb_harvested}/{nb_total} (~{round(nb_harvested/nb_total, 2) * 100}%)")

def domain_stats(stats):
    b = [[stat['entry']['url'], stat['is_harvested']] for stat in stats]
    b = pd.DataFrame(b, columns=['url', 'is_harvested'])
    b['domain'] = b.url.str.extract(r'https?://(.*?)/.*')
    b['is_harvested'] = b['is_harvested'].apply(int)
    return b[['domain', 'is_harvested']].groupby('domain').agg({'count', 'sum'})['is_harvested']

if __name__ == "__main__":
    log_filepath = './logs/harvester.log'
    stats_filepath = './logs/stats.jsonl'
    stats = extract_stats_from_logs(log_filepath)
    write_jsonl(stats, stats_filepath)
    # stats = read_stats_file(stats_filepath)
    summary(stats)
    domain_stats(stats).to_csv('domains_stats.csv')