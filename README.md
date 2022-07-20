# Publication PDF harvester and metadata extractor.

This project aims to download french scientific publications and process them using Deep Learning models ([Grobid](https://hub.docker.com/r/grobid/grobid), [Softcite](https://hub.docker.com/r/grobid/software-mentions) and [Datastet](https://hub.docker.com/r/grobid/datastet)) to extract metadata relevant for the Baromètre de la Science Ouverte (BSO).  
It uses as input a filtered subset of the [Unpaywall database snapshot](https://unpaywall.org) (from [OurResearch](http://ourresearch.org/)) stored on an OVH objecct storage.

The harvester part of this repo is based of a fork of the repo https://github.com/kermitt2/biblio-glutton-harvester but has been heavily modified to fit the needs of this project.
The processing part uses a [python client for Grobid](https://github.com/kermitt2/grobid_client_python) and a [python client for Softcite and Datastet](https://github.com/kermitt2/softdata_mentions_client) to handle the communication with the containers exposing the different deep learning models.

* The downloaded PDF can be stored on a SWIFT object storage (OpenStack) or on a local storage, with UUID
  renaming/mapping.

* Downloads and storage uploads over HTTP(S) are multi-threaded for best robustness and efficiency.

* The download supports redirections, https protocol, wait/retries, uses rotating request headers and resolve cloudflare v1 challenges.

* The harvesting process can be interrupted and resumed.

* The tool is fault tolerant, it will keep track of the failed resource access with corresponding errors and makes
  possible subsequent retry on this subset.

* A postgres database can track the harvesting of the publications harvested when launched with docker-compose. It contains the UUID/DOI mapping, the url used to download the publication, the date of the download and informations about the processing services.

* The publications can then be processed by the Grobid model, Softcite model and Datastet model to extract metadatas. The version of each of the services used are recorded in the postgres database.

* The output of each model is stored in a file on a SWIFT object storage.

## Environment setup

### Requirements

The utility requires Python 3.6 or more. It is developed for a deployment on a POSIX/Linux server (`gzip` and `wget` as
external process). A SWIFT object storage and a dedicated SWIFT container must have been created for the cloud storage
of the data collection.

The utility will use some local storage dedicated to the embedded databases keeping track of the advancement of the
harvesting, metadata and temporary downloaded resources. Consider a few GB of free space for a large scale harvesting of
TB of PDF.

Storage: as a rule of thumb, consider bewteen 1 and 1.5 TB for storage 1 million scholar PDF.

### Install

1. Get the github repository:

```shell
$ git clone https://github.com/Barometre-de-la-Science-Ouverte/bso3-harvest-publication.git
$ cd bso3-harvest-publication
```

2. Setup the Python virtual environment

```shell
$ virtualenv --system-site-packages -p python3 env
$ source env/bin/activate
$ make install
```

3. Add the configuration files for *arxiv* (arxiv_config.py) and *wiley* (wiley_config.py) to the config folder (ask a
   developer for them).

## Configuration

A configuration file must be completed, by default the file `config.json` will be used, but it is also possible to use
it as a template and specifies a particular configuration file when using the tool (via the `--config` parameter).

- `compression` indicates if the resource files need to be compressed with `gzip` or not. Default is true, which means
  that all the harvested files will have an additional extension `.gz`.

- `batch_size` gives the number of PDF that is considered for parallel process at the same time, the process will move
  to a new batch only when all the PDF of the previous batch will be processed.

- `metadata_dump` is the bucket containing the metadata files of the publications to be harvested.

- `is_level_debug` indicates the logging level.

```json
{
    "compression": true,
    "batch_size": 200,
    "metadata_dump": "",
    "lmdb_size_Go": 25,
    "is_level_debug": 1
}
```
Other elements of configuration need to be provided by environment variables.  

Variables for connecting to OVH storage via the [swift openstack API](https://docs.ovh.com/fr/storage/debuter-avec-lapi-swift/). It contains the account and authentication information (authentication is made via Keystone):
```
# swift - ovh
OS_USERNAME
OS_PASSWORD
OS_USER_DOMAIN_NAME
OS_PROJECT_DOMAIN_NAME
OS_PROJECT_NAME
OS_PROJECT_ID
OS_REGION_NAME
OS_AUTH_URL
```
If you are not using a SWIFT storage, leave these above values empty.

The name of the swift object storage where the harvested publications will be stored:
```
PUBLICATIONS_DUMP_BUCKET
```
Variables for the postgres storage tracking the harvested files:
```
# Postgres
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
DB_NAME
```
Variables for harvesting Wiley publications via their API:
```
# Wiley
CONFIG_WILEY_TOKEN_KEY
CONFIG_WILEY_EZPROXY_USER_KEY
CONFIG_WILEY_EZPROXY_PASS_KEY
CONFIG_WILEY_PUBLICATION_URL_KEY
CONFIG_WILEY_BASE_URL_KEY
```

## Usage and options

Current usage assume a containerised setup (as can be seen in the docker-compose.yml file):
- A version of this application run in web application (flask) mode that schedule harvesting or processing tasks based on the requests received.
- A version of this application run in worker mode that fetch tasks in a queue and executes them.
- A redis container to register tasks on.
- A [dashboard web app](https://hub.docker.com/r/dataesr/dashboard-crawler) that displays informations on queues, tasks and worker.
- A postgres container to record harvested publications infos. 

```
# Build the image and spin up the containers
docker-compose up --build
# When everything is up and running
# Schedule a harvesting task with a request on the harvest_partitions route
curl  -H "Content-Type: application/json" -X POST http://localhost:5004/harvest_partitions -d '{"metadata_file": "your_metadata_file.jsonl.gz", "total_partition_number": X}'
# Or schedule a processing task with a request on the process route
curl  -H "Content-Type: application/json" -X POST http://localhost:5004/process -d '{"partition_size": X, "spec_grobid_version": "X.Y.Z", "spec_softcite_version": "X.Y.Z", "spec_datastet_version": "X.Y.Z"}'
```

Documentation of the endpoints is available at `http://localhost:5004` once your app is running

## Storage

Files are stored under a path like format on OVH object storage to be able to access a subset quickly. The different files generated by this project are organised as follow:
```
prefix/uuid[0:2]/uuid[2:4]/uuid[4:6]/uuid[6:8]/uuid/uuid.ext
```
prefix can be one of `metadata`, `publication`, `datastet`, `softcite`, `grobid` indicating its type and allowing for efficient access for the needs of the BSO.


## License and contact

Distributed under [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0). The dependencies used in the project
are either themselves also distributed under Apache 2.0 license or distributed under a compatible license.

If you contribute to this Open Source project, you agree to share your contribution following this license.
