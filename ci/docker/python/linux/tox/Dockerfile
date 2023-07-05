FROM ubuntu:20.04 as wheel_builder_base
COPY ci/docker/python/linux/tox/apt-packages.txt /tmp/
RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    < /tmp/apt-packages.txt xargs apt-get install -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL


# ==============================================================================
FROM wheel_builder_base as WHEEL_BUILDER_PY38
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY requirements.txt  requirements-dev.txt requirements-freeze.txt ci/docker/python/shared/requirements-ci.txt ci/docker/python/shared/requirements-extra.txt /tmp/
COPY requirements /tmp/requirements
ENV PYTHON=python3.8
RUN $PYTHON -m venv venv && \
    . ./venv/bin/activate && \
    python -m pip install --no-cache-dir wheel==0.37.1 && \
    python -m pip wheel -w /wheels --no-cache-dir  \
        -r /tmp/requirements.txt \
        -r /tmp/requirements-dev.txt  \
        -r /tmp/requirements-ci.txt  \
        -r /tmp/requirements-extra.txt && \
    rm -rf venv

# ==============================================================================
FROM wheel_builder_base as WHEEL_BUILDER_PY39
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY requirements.txt  requirements-dev.txt requirements-freeze.txt ci/docker/python/shared/requirements-ci.txt ci/docker/python/shared/requirements-extra.txt /tmp/
COPY requirements /tmp/requirements
ENV PYTHON=python3.9
RUN $PYTHON -m venv venv && \
    . ./venv/bin/activate && \
    python -m pip install --no-cache-dir wheel==0.37.1 && \
    python -m pip wheel -w /wheels --no-cache-dir  \
        -r /tmp/requirements.txt \
        -r /tmp/requirements-dev.txt  \
        -r /tmp/requirements-ci.txt  \
        -r /tmp/requirements-extra.txt && \
    rm -rf venv

# ==============================================================================
FROM wheel_builder_base as WHEEL_BUILDER_PY310
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY requirements.txt  requirements-dev.txt requirements-freeze.txt ci/docker/python/shared/requirements-ci.txt ci/docker/python/shared/requirements-extra.txt /tmp/
COPY requirements /tmp/requirements
ENV PYTHON=python3.10
RUN $PYTHON -m ensurepip --upgrade && \
    $PYTHON -m venv venv && \
    . ./venv/bin/activate && \
    python -m pip install --no-cache-dir wheel==0.37.1 && \
    python -m pip wheel -w /wheels --no-cache-dir  \
        -r /tmp/requirements.txt \
        -r /tmp/requirements-dev.txt  \
        -r /tmp/requirements-ci.txt  \
        -r /tmp/requirements-extra.txt && \
    rm -rf venv


# ==============================================================================
FROM wheel_builder_base as WHEEL_BUILDER_PY311
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

COPY requirements.txt  requirements-dev.txt requirements-freeze.txt ci/docker/python/shared/requirements-ci.txt ci/docker/python/shared/requirements-extra.txt /tmp/
COPY requirements /tmp/requirements
ENV PYTHON=python3.11
RUN $PYTHON -m ensurepip --upgrade && \
    $PYTHON -m venv venv && \
    . ./venv/bin/activate && \
    python -m pip install --no-cache-dir wheel==0.37.1 && \
    python -m pip wheel -w /wheels --no-cache-dir  \
        -r /tmp/requirements.txt \
        -r /tmp/requirements-dev.txt  \
        -r /tmp/requirements-ci.txt  \
        -r /tmp/requirements-extra.txt && \
    rm -rf venv


# ==============================================================================
FROM wheel_builder_base
RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
COPY --from=WHEEL_BUILDER_PY38 /wheels/* /wheels/
COPY --from=WHEEL_BUILDER_PY39 /wheels/* /wheels/
COPY --from=WHEEL_BUILDER_PY310 /wheels/* /wheels/
COPY --from=WHEEL_BUILDER_PY311 /wheels/* /wheels/
ENV PIP_FIND_LINKS=/wheels
COPY requirements /tmp/
RUN pip3 install -r /tmp/requirements_tox.txt "devpi-client<6.0" build
WORKDIR /src
CMD tox --workdir /tmp/tox --recreate
