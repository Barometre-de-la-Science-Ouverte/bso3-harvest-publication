## Docker image for biblio-glutton-fixtures

## See https://github.com/kermitt2/biblio-glutton-harvester

# the python slim image does not include gcc, which is required to install python packages
# and installing additional dependencies with apt-get appears unstable
FROM python:3.8

# setting locale is likely useless but to be sure
ENV LANG C.UTF-8

# USER root

RUN python3 -m pip install pip --upgrade

WORKDIR /src

# copy project
COPY config.json .
COPY requirements.txt .

RUN mkdir /src/data
RUN mkdir /src/tmp

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install git+https://github.com/Barometre-de-la-Science-Ouverte/grobid_client_python.git#egg=grobid_client_python
RUN pip install git+https://github.com/Barometre-de-la-Science-Ouverte/software_mentions_client#egg=software_mentions_client

COPY . .

# for interactive CLI usage of the image
CMD ["bash"]
