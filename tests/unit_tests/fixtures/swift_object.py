import json
from infrastructure.storage.swift import Swift
from config.harvester_config import config_harvester

_swift = Swift(config_harvester)

local_dir = [
    './tmp/downloaded_publications/9fea8e3a-344c-4552-874c-6852074bcdd1.json',
    './tmp/downloaded_publications/9fea8e3a-344c-4552-874c-6852074bcdd1.pdf',
    './tmp/downloaded_publications/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.json',
    './tmp/downloaded_publications/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.pdf'
]

files_to_upload = [
    ('./tmp/downloaded_publications/9fea8e3a-344c-4552-874c-6852074bcdd1.json', 'processed/9f/ea/8e/3a/9fea8e3a-344c-4552-874c-6852074bcdd1/9fea8e3a-344c-4552-874c-6852074bcdd1.json'),
    ('./tmp/downloaded_publications/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.json', 'processed/dc/d4/1f/3e/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.json'),
]