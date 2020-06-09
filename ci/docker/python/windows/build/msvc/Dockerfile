# escape=`
ARG PYTHON_DOCKER_IMAGE_BASE=python:3.7
FROM ${PYTHON_DOCKER_IMAGE_BASE} as wheel_builder


ADD requirements.txt requirements-freeze.txt requirements-dev.txt c:/temp/

ENV PIP_EXTRA_INDEX_URL="https://devpi.library.illinois.edu/production/release"
RUN python -m pip install pip --upgrade ; `
    python -m pip install setuptools --upgrade ; `
    python -m pip install wheel ; `
    python -m pip wheel --wheel-dir=c:\temp\wheels `
                        -r c:\temp\requirements.txt `
                        -r c:\temp\requirements-dev.txt `
                        -r c:\temp\requirements-freeze.txt `
                        tox
RUN python -m pip wheel --wheel-dir=c:\temp\wheels `
    pykdu_compress --pre

FROM ${PYTHON_DOCKER_IMAGE_BASE}
RUN certutil -generateSSTFromWU roots.sst ; `
    certutil -addstore -f root roots.sst ; `
    del roots.sst
COPY --from=wheel_builder c:\temp\wheels c:\wheels\
ENV PIP_EXTRA_INDEX_URL="https://devpi.library.illinois.edu/production/release"
ENV PIP_TRUSTED_HOST="devpi.library.illinois.edu"
ENV PIP_FIND_LINKS=c:\wheels\
ADD requirements.txt requirements-freeze.txt requirements-dev.txt c:/temp/
RUN python -m pip install pip --upgrade ; `
    python -m pip install setuptools --upgrade ; `
    python -m pip install -r c:\temp\requirements.txt `
                          -r c:\temp\requirements-freeze.txt `
                          tox ; `
    python -m pip install pykdu_compress --pre