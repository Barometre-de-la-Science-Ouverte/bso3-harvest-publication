import os
import requests
import redis

from flask import Blueprint, current_app, jsonify, render_template, request
from rq import Connection, Queue
from application.server.main.tasks import create_task_unpaywall

default_timeout = 43200000

main_blueprint = Blueprint('main', __name__, )

@main_blueprint.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@main_blueprint.route('/harvest', methods=['POST'])
def run_task_unpaywall():
    """
    Harvest data from unpaywall
    """
    args = request.get_json(force=True)
    with Connection(redis.from_url(current_app.config['REDIS_URL'])):
        q = Queue(name='pdf-harvester', default_timeout=default_timeout)
        task = q.enqueue(create_task_unpaywall, args)
    response_object = {
        'status': 'success',
        'data': {
            'task_id': task.get_id()
        }
    }
    return jsonify(response_object)


    response_object = {
        'status': 'success'
    }

    return jsonify(response_object), 202


@main_blueprint.route('/tasks/<task_id>', methods=['GET'])
def get_status(task_id):
    with Connection(redis.from_url(current_app.config['REDIS_URL'])):
        q = Queue('pdf-harvester')
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
