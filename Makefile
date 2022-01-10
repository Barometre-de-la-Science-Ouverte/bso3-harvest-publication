DOCKER_IMAGE_NAME=dataesr/bso3-harvest-publication
CURRENT_VERSION=$(shell cat application/__init__.py | cut -d "'" -f 2)

docker-build:
	@echo Building a new docker image
	docker build -t $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION) -t $(DOCKER_IMAGE_NAME):latest .
	@echo Docker image built

docker-push:
	@echo Pushing a new docker image
	docker push $(DOCKER_IMAGE_NAME):$(CURRENT_VERSION)
	docker push $(DOCKER_IMAGE_NAME):latest
	@echo Docker image pushed

install:
	@echo Installing dependencies...
	pip install -r requirements.txt
	@echo End of dependencies installation
