import redis
from flask import Blueprint, current_app, jsonify, render_template, request
from rq import Connection, Queue

from application.server.main.tasks import (create_task_process,
                                           create_task_unpaywall)
from config.harvester_config import config_harvester
from infrastructure.storage.swift import Swift
from ovh_handler import get_partitions

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
    return jsonify(response_object), 202


@main_blueprint.route('/harvester_tasks/<task_id>', methods=['GET'])
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


@main_blueprint.route('/process', methods=['POST'])
def run_task_process():
    """
    Process publications using Grobid and Softcite
    """
    args = request.get_json(force=True)
    partition_size = args.get('partition_size', 1_000)
    break_after_one = args.get('break_after_one', True)
    storage_handler = Swift(config_harvester)
    partitions = get_partitions(storage_handler, partition_size)
    with Connection(redis.from_url(current_app.config['REDIS_URL'])):
        q = Queue(name='pdf-processor', default_timeout=default_timeout)
        for partition in partitions:
            task = q.enqueue(create_task_process, storage_handler, partition)
            if break_after_one:
                break
    response_object = {
        'status': 'success',
        'data': {
            'task_id': task.get_id()
        }
    }
    return jsonify(response_object)


@main_blueprint.route('/processor_tasks/<task_id>', methods=['GET'])
def get_status(task_id):
    with Connection(redis.from_url(current_app.config['REDIS_URL'])):
        q = Queue('pdf-processor')
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
