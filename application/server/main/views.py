import redis
from flask import Blueprint, current_app, jsonify, render_template, request
from rq import Connection, Queue

from application.server.main.logger import get_logger
from application.server.main.tasks import create_task_process, create_task_harvest_partition
from config import WILEY_KEY
from config.harvester_config import config_harvester
from config.logger_config import LOGGER_LEVEL
from harvester.exception import FailedRequest
from harvester.wiley_client import WileyClient
from infrastructure.storage.swift import Swift
from ovh_handler import get_partitions

HOURS = 3600

default_timeout = 6 * HOURS

main_blueprint = Blueprint("main", __name__)
logger = get_logger(__name__, level=LOGGER_LEVEL)


@main_blueprint.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@main_blueprint.route("/harvest_partitions", methods=["POST"])
def run_task_harvest_partitions():
    args = request.get_json(force=True)
    source_metadata_file = args.get("metadata_file")
    total_partition_number = args.get("total_partition_number")
    doi_list = args.get("doi_list", [])
    response_objects = []
    try:
        wiley_client = WileyClient(config_harvester[WILEY_KEY])
    except FailedRequest:
        wiley_client = None
        logger.error("Did not manage to initialize the wiley_client. The wiley_client instance will be set to None"
                     " and standard download will be used in the case of a wiley URL."
                     " Request exception = ", exc_info=True)
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue(name="pdf-harvester", default_timeout=default_timeout)
        for partition_index in range(total_partition_number + 1):
            task_kwargs = {
                "source_metadata_file": source_metadata_file,
                "partition_index": partition_index,
                "total_partition_number": total_partition_number,
                "doi_list": doi_list,
                "job_timeout": 3 * HOURS,
                "wiley_client": wiley_client
            }
            task = q.enqueue(create_task_harvest_partition, **task_kwargs)
            response_objects.append({"status": "success", "data": {"task_id": task.get_id()}})
    return jsonify(response_objects)


@main_blueprint.route("/harvester_tasks/<task_id>", methods=["GET"])
def get_status_harvester(task_id):
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue("pdf-harvester")
        task = q.fetch_job(task_id)
    if task:
        response_object = {
            "status": "success",
            "data": {
                "task_id": task.get_id(),
                "task_status": task.get_status(),
                "task_result": task.result,
            },
        }
    else:
        response_object = {"status": "error"}
    return jsonify(response_object)


@main_blueprint.route("/process", methods=["POST"])
def run_task_process():
    """
    Process publications using Grobid, Softcite and Datastet
    """
    args = request.get_json(force=True)
    partition_size = args.get("partition_size", 1_000)
    spec_grobid_version = args.get("spec_grobid_version", "0")
    spec_softcite_version = args.get("spec_softcite_version", "0")
    spec_datastet_version = args.get("spec_datastet_version", "0")
    break_after_one = args.get("break_after_one", False)
    storage_handler = Swift(config_harvester)
    partitions = get_partitions(storage_handler, partition_size)
    response_objects = []
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue(name="pdf-processor", default_timeout=default_timeout)
        for partition in partitions:
            task = q.enqueue(
                create_task_process,
                kwargs={
                    "partition_files": partition,
                    "spec_grobid_version": spec_grobid_version,
                    "spec_softcite_version": spec_softcite_version,
                    "spec_datastet_version": spec_datastet_version,
                },
            )
            response_objects.append({"status": "success", "data": {"task_id": task.get_id()}})
            if break_after_one:
                break
    return jsonify(response_objects)


@main_blueprint.route("/processor_tasks/<task_id>", methods=["GET"])
def get_status_processing(task_id):
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue("pdf-processor")
        task = q.fetch_job(task_id)
    if task:
        response_object = {
            "status": "success",
            "data": {
                "task_id": task.get_id(),
                "task_status": task.get_status(),
                "task_result": task.result,
            },
        }
    else:
        response_object = {"status": "error"}
    return jsonify(response_object)
