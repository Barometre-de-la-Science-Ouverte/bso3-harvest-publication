DOCKER_IMAGE_NAME=dataesr/bso3-harvest-publication
CURRENT_VERSION=$(shell cat application/__init__.py | cut -d "'" -f 2)
LOCAL_ENDPOINT="http://127.0.0.1:5004/harvest_partitions"
PAYLOAD='{"metadata_file": "bso-publications-5k.jsonl.gz", "total_partition_number": 2, "doi_list": ["10.1111/jdv.15719", "10.1016/s1773-035x(19)30258-8", "10.1016/s2055-6640(20)30035-2"]}'
ENV_VARIABLE_FILENAME=.env

unit-tests:
	pytest --disable-warnings tests

e2e-tests:
	@echo Start end-to-end testing
	docker-compose up -d --build
	sleep 30
	behave ./tests/e2e_tests/features
	docker-compose down

lint: lint-syntax lint-style

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

docker-build: clean_up_files
	cat config.json
	./confirm_before_build.sh

docker-build-local-image:
	@echo Building a local image
	docker build -t $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION)_local -t $(DOCKER_IMAGE_NAME):latest_local -f ./Dockerfiles/dev/. .
	@echo Docker image built

docker-build-prod-image:
	@echo Building a prod image
	docker build -t $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION) -t $(DOCKER_IMAGE_NAME):latest -f ./Dockerfiles/prod/. .
	@echo Docker image built

docker-push:
	@echo Pushing the prod image
	docker push $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION)
	docker push $(DOCKER_IMAGE_NAME):latest
	@echo Docker image pushed

set-env-variables:
	export $(grep -v '^#' $(ENV_VARIABLE_FILENAME) | xargs)

unset-env-variables:
	unset $(grep -v '^#' .env | sed -E 's/(.*)=.*/\1/' | xargs)

install:
	@echo Installing dependencies...
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo End of dependencies installation

requirements:
	pipreqs . --savepath requirements.in
	grep -v "software_mentions_client" requirements.in > requirements_tmp; mv requirements_tmp requirements.in
	grep -v "grobid_client" requirements.in > requirements_tmp; mv requirements_tmp requirements.in
	grep -v "testing" requirements.in > requirements_tmp; mv requirements_tmp requirements.in
	echo "python-keystoneclient==4.0.0" >> requirements.in
	echo "testing.postgresql==1.3.0" >> requirements.in
	pip-compile requirements.in
	rm requirements.in
	# echo "# Grobid client package" >> requirements.txt
	# echo "git+https://github.com/Barometre-de-la-Science-Ouverte/grobid_client_python.git#egg=grobid_client_python" >> requirements.txt
	# echo "# Softcite client package" >> requirements.txt
	# echo "git+https://github.com/Barometre-de-la-Science-Ouverte/software_mentions_client#egg=software_mentions_client" >> requirements.txt
