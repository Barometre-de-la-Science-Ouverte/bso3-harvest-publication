import json
import os

from flask import Flask, jsonify

from config.path_config import CONFIG_PATH, PROJECT_DIRNAME
from harvester.OAHarvester import OAHarvester
# from load_metadata import load_metadata

app = Flask(__name__)

@app.route('/unpaywall', methods=['GET'])
def run_task_unpaywall():
    """
    Harvest data from unpaywall
    """
    # archive_path = load_metadata()
    archive_path = os.path.join(PROJECT_DIRNAME, 'tmp', 'bso-publications-staging_20211119_sample_5k.jsonl.gz')
    config_harvester = json.load(open(CONFIG_PATH, 'r'))
    harvester = OAHarvester(config_harvester, thumbnail=False, sample=100, sample_seed=1)
    harvester.harvestUnpaywall(archive_path)
    """
    with Connection(redis.from_url(current_app.config['REDIS_URL'])):
        q = Queue('unpaywall', default_timeout=DEFAULT_TIMEOUT)
        task = q.enqueue(harvester.harvestUnpaywall, archive_path)
    """
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
