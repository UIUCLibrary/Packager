# escape=`
ARG PYTHON_DOCKER_IMAGE_BASE=python:3.7
FROM ${PYTHON_DOCKER_IMAGE_BASE} as wheel_builder



ENV PIP_EXTRA_INDEX_URL="https://devpi.library.illinois.edu/production/release/"
ENV PIP_TRUSTED_HOST="devpi.library.illinois.edu"
RUN python -m pip install pip --upgrade ; `
    python -m pip install wheel ; `
    python -m pip install setuptools --upgrade

ADD requirements.txt requirements-freeze.txt ci/docker/python/shared/requirements-ci.txt c:/temp/

RUN pip wheel --wheel-dir=c:\temp\wheels `
                        -r c:/temp/requirements.txt `
                        -r c:/temp/requirements-ci.txt `
                        -r c:/temp/requirements-freeze.txt


FROM ${PYTHON_DOCKER_IMAGE_BASE}
RUN certutil -generateSSTFromWU roots.sst ; `
    certutil -addstore -f root roots.sst ; `
    del roots.sst

COPY --from=wheel_builder c:\temp\wheels c:\wheels\

ENV PIP_EXTRA_INDEX_URL="https://devpi.library.illinois.edu/production/release"
ENV PIP_TRUSTED_HOST="devpi.library.illinois.edu"

RUN python -m pip install pip --upgrade ; `
    python -m pip install wheel ; `
    python -m pip install setuptools --upgrade

ADD requirements.txt requirements-freeze.txt ci/docker/python/shared/requirements-ci.txt c:/temp/

RUN python -m pip install --find-links c:\wheels\ `
        -r c:\temp\requirements.txt `
        -r c:\temp\requirements-freeze.txt `
        -r c:\temp\requirements-ci.txt

ENV PIP_FIND_LINKS=c:\wheels\