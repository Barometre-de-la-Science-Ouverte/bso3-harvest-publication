from flask import Flask, jsonify

import load_metadata
from config.harvester_config import config_harvester, NB_SAMPLE_TO_HARVEST
from config.path_config import INPUT_METADATA_PATH
from config.storage_config import METADATA_DUMP, DESTINATION_DIR_METADATA
from harvester.OAHarvester import OAHarvester
from load_metadata import load_metadata

app = Flask(__name__)


@app.route('/unpaywall', methods=['GET'])
def run_task_unpaywall():
    """
    Harvest data from unpaywall
    """

    harvester = OAHarvester(config_harvester, thumbnail=False, sample=NB_SAMPLE_TO_HARVEST, sample_seed=1)

    if len(METADATA_DUMP) > 0:
        metadata_file = load_metadata(METADATA_DUMP, DESTINATION_DIR_METADATA)
    else:
        metadata_file = INPUT_METADATA_PATH

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
