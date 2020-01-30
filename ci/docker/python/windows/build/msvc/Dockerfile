# escape=`
ARG PYTHON_DOCKER_IMAGE_BASE=python:3.7
FROM ${PYTHON_DOCKER_IMAGE_BASE}

RUN certutil -generateSSTFromWU roots.sst ; `
    certutil -addstore -f root roots.sst ; `
    del roots.sst

ADD requirements.txt requirements-freeze.txt requirements-dev.txt c:/temp/

ENV PIP_EXTRA_INDEX_URL="https://devpi.library.illinois.edu/production/release"
RUN python -m pip install pip --upgrade ; python -m pip install -r c:\temp\requirements.txt -r c:\temp\requirements-dev.txt -r c:\temp\requirements-freeze.txt coverage flake8 lxml
RUN python -m pip install setuptools --upgrade
