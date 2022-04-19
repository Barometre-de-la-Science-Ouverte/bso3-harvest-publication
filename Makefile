DOCKER_IMAGE_NAME=dataesr/bso3-harvest-publication
CURRENT_VERSION=$(shell cat application/__init__.py | cut -d "'" -f 2)
LOCAL_ENDPOINT="http://127.0.0.1:5004/harvest_partitions"
PAYLOAD='{"metadata_file": "bso-publications-5k.jsonl.gz", "total_partition_number": 2, "doi_list": ["10.1111/jdv.15719"]}'

clean_up_files:
	rm -rf logs/*
	rm -rf downloaded_publications
	rm -rf lmdb/entries_software
	rm -rf data/
	rm -rf tmp/*
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf */*/__pycache__/
	rm -rf */*/*/__pycache__/
	rm -rf *.pyc
	rm -rf */*.pyc
	rm -rf */*/*.pyc
	rm -rf */*/*/*.pyc
	rm -rf .ipynb_checkpoints/

docker-build: clean_up_files
	cat config.json | jq
	./confirm_before_build.sh

docker-build-local-image:
	@echo Building a local image
	docker build -t $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION)_local -t $(DOCKER_IMAGE_NAME):latest_local .
	@echo Docker image built

docker-build-prod-image:
	@echo Building a prod image
	docker build -t $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION) -t $(DOCKER_IMAGE_NAME):latest .
	@echo Docker image built

docker-push:
	@echo Pushing the prod image
	docker push $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION)
	docker push $(DOCKER_IMAGE_NAME):latest
	@echo Docker image pushed

docker-up:
	@echo Start end-to-end testing
	docker-compose up -d
	sleep 15
	curl -d $(PAYLOAD) -H "Content-Type: application/json" -X POST $(LOCAL_ENDPOINT)
	sleep 200
	records_counts_table=$(docker exec -e PGPASSWORD=password-dataESR-bso3 -i $(docker ps --filter "NAME=postgres" -q) psql -d postgres_db -U postgres -c 'SELECT count(*) FROM harvested_status_table LIMIT 1;' | awk 'FNR == 3 {print $1}')
	if [[ "$records_counts_table" -eq "0" ]]; then echo "Test failure no records in postgres..."; else echo "Test success : record in postgres..."; fi

install: requirements
	@echo Installing dependencies...
	pip install -r requirements.txt
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

kube-count-nb-publications-in-db:
	kubectl exec $(kubectl get pods -n default --no-headers=true | awk '/postgres/{print $1}') -- psql -d postgres_db -U postgres -c 'SELECT count(*) FROM harvested_status_table LIMIT 1;'
