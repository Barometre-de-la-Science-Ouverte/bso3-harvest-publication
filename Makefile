DOCKER_IMAGE_NAME=dataesr/bso3-harvest-publication
CURRENT_VERSION=$(shell cat application/__init__.py | cut -d "'" -f 2)
ENV_VARIABLE_FILENAME=.env

.PHONY: help

.DEFAULT_GOAL := help

help:
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

unit-tests: ## run unit tests
	python3 -m pytest --disable-warnings tests

e2e-tests: ## run end-to-end tests
	@echo Start end-to-end testing
	docker-compose up -d --build
	sleep 30
	behave ./tests/e2e_tests/features
	docker-compose down

lint: lint-syntax lint-style ## run linter

lint-style:
	@echo Checking style errors - PEP 8
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=200 --statistics

lint-syntax:
	@echo Checking syntax errors
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

clean_up_files:
	rm -rf logs/*
	rm -rf downloaded_publications
	rm -rf lmdb/entries_software
	rm -rf data/
	rm -rf tmp/*
	find . | grep -E "(__pycache__|\.pyc|\.pyo)" | xargs rm -rf
	rm -rf .ipynb_checkpoints/
	find . -iname \*.ipynb | xargs -I filename nbdev_clean --clear_all --fname filename

docker-build: ## Build either a docker image for local or prod use
	./confirm_before_build.sh

docker-build-local-image: clean_up_files ## Build a docker image for local use
	@echo Building a local image
	docker build -t $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION)_local -t $(DOCKER_IMAGE_NAME):latest_local -f ./Dockerfiles/dev/. .
	@echo Docker image built

docker-build-prod-image: clean_up_files ## Build a docker image for prod use
	@echo Building a prod image
	docker build -t $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION) -t $(DOCKER_IMAGE_NAME):latest -f ./Dockerfiles/prod/. .
	@echo Docker image built

docker-push: ## Push the image with the current version tag and latest tag to the dataesr repository
	@echo Pushing the prod image
	docker push $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION)
	docker push $(DOCKER_IMAGE_NAME):latest
	@echo Docker image pushed

download-harvested-status-table-csv: ## Download the harvested_status_table from postgres
	@kubectl exec postgresql-0 -- psql -d postgres_db -U postgres -c "\copy harvested_status_table to './harvested_status_table.csv' with csv;"
	@kubectl exec postgresql-0 -- gzip -c ./harvested_status_table.csv > ./tmp/pg_dump/harvested_status_table.csv.gz
	@kubectl exec postgresql-0 -- rm ./harvested_status_table.csv

# kubectl cp is really just a thin wrapper on kubectl exec plus tar. (https://github.com/kubernetes/kubernetes/issues/60140#issuecomment-952168803)
# What worked for me, is to base64 encode the data on the fly. (https://github.com/kubernetes/kubernetes/issues/60140#issuecomment-1039049831)
download-last-dump: ## Download the last postgres dump
	@echo Downloading the last pg dump
	@kubectl exec postgresql-0 -- ls -tlh /var/lib/postgresql/backup/ | awk 'NR==2'
	@echo to ./tmp/pg_dump/
	@kubectl exec postgresql-0 -- base64 /var/lib/postgresql/backup/$(shell kubectl exec postgresql-0 -- ls -t /var/lib/postgresql/backup/ | awk 'NR==1') | base64 -d > ./tmp/pg_dump/last_pg_dump.gz

set-env-variables: ## Set up the environment variables
	@echo Setting up environment variables
	export $(grep -v '^#' $(ENV_VARIABLE_FILENAME) | xargs)

unset-env-variables: ## Unset the environment variables
	unset $(grep -v '^#' .env | sed -E 's/(.*)=.*/\1/' | xargs)

install: ## Install python dependencies
	@echo Installing dependencies...
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	nbdev_install_hooks
	@echo End of dependencies installation

requirements: ## Automatically generate requirements.txt based on the codebase
	pipreqs . --savepath requirements.in
	grep -v "behave" requirements.in > requirements_tmp; mv requirements_tmp requirements.in
	grep -v "pandas" requirements.in > requirements_tmp; mv requirements_tmp requirements.in
	grep -v "softdata_mentions_client" requirements.in > requirements_tmp; mv requirements_tmp requirements.in
	grep -v "grobid_client" requirements.in > requirements_tmp; mv requirements_tmp requirements.in
	grep -v "testing" requirements.in > requirements_tmp; mv requirements_tmp requirements.in
	echo "python-keystoneclient==4.0.0" >> requirements.in
	echo "testing.postgresql==1.3.0" >> requirements.in
	echo "alembic==1.8.0" >> requirements.in
	pip-compile requirements.in
	rm requirements.in
	echo "" >> requirements.txt
	echo "# Grobid client package" >> requirements.txt
	echo "git+https://github.com/Barometre-de-la-Science-Ouverte/grobid_client_python.git#egg=grobid_client_python" >> requirements.txt
	echo "# Softcite & Datastet client package" >> requirements.txt
	echo "git+https://github.com/Barometre-de-la-Science-Ouverte/softdata_mentions_client.git#egg=softdata_mentions_client" >> requirements.txt
