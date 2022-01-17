import os

from flask import Flask, jsonify

import load_metadata
from config.harvester_config import config_harvester
from config.path_config import METADATA_FILE, DESTINATION_DIR_METADATA
from harvester.OAHarvester import OAHarvester
from load_metadata import load_metadata

METADATA_DUMP = config_harvester['metadata_dump']
NB_SAMPLES = config_harvester['nb_samples_to_harvest']

app = Flask(__name__)

@app.route('/unpaywall', methods=['GET'])
def run_task_unpaywall():
    """
    Harvest data from unpaywall
    """

    harvester = OAHarvester(config_harvester, thumbnail=False, sample=NB_SAMPLES, sample_seed=1)

    if len(METADATA_DUMP) > 0:
        metadata_file = load_metadata(metadata_container=METADATA_DUMP,
                                      metadata_file=METADATA_FILE,
                                      destination_dir=DESTINATION_DIR_METADATA)
    else:
        metadata_file = os.path.join(DESTINATION_DIR_METADATA, METADATA_FILE)

    harvester.harvestUnpaywall(metadata_file)

    response_object = {
        'status': 'success'
    }

    return jsonify(response_object), 202


"""
@main_blueprint.route('/unpaywall/tasks/<task_id>', methods=['GET'])
def get_status(task_id):
    with Connection(redis.from_url(current_app.config['REDIS_URL'])):
        q = Queue('unpaywall')
        task = q.fetch_job(task_id)
    if task:
        response_object = {
            'status': 'success',
            'data': {
                'task_id': task.get_id(),
                'task_status': task.get_status(),
                'task_result': task.result,
            }
        }
    else:
        response_object = {'status': 'error'}
    return jsonify(response_object)
"""
