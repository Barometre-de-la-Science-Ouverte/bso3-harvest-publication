import json
import os
from infrastructure.storage.swift import Swift
from config.harvester_config import config_harvester

_swift = Swift(config_harvester)

local_dir = [
    './tmp/downloaded_publications/9fea8e3a-344c-4552-874c-6852074bcdd1.json',
    './tmp/downloaded_publications/9fea8e3a-344c-4552-874c-6852074bcdd1.software.json',
    './tmp/downloaded_publications/9fea8e3a-344c-4552-874c-6852074bcdd1.tei.xml',
    './tmp/downloaded_publications/9fea8e3a-344c-4552-874c-6852074bcdd1.pdf',
    './tmp/downloaded_publications/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.software.json',
    './tmp/downloaded_publications/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.tei.xml',
    './tmp/downloaded_publications/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.json',
    './tmp/downloaded_publications/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.pdf'
]

softcite_files_to_upload = [
    ('./tmp/downloaded_publications/9fea8e3a-344c-4552-874c-6852074bcdd1.software.json',
     os.path.join('softcite','9f', 'ea', '8e', '3a', '9fea8e3a-344c-4552-874c-6852074bcdd1', '9fea8e3a-344c-4552-874c-6852074bcdd1.software.json')),
    ('./tmp/downloaded_publications/dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.software.json',
     os.path.join('softcite', 'dc', 'd4', '1f', '3e', 'dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38', 'dcd41f3e-4dcb-41b4-8d60-bc8abce3ee38.software.json')),
]