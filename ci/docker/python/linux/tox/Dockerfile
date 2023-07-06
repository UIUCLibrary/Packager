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


FROM wheel_builder_base
RUN mkdir -p /.cache/pip && \
    chmod -R 777 /.cache
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ENV PIP_FIND_LINKS=/wheels
COPY requirements /tmp/
RUN pip3 install -r /tmp/requirements_tox.txt devpi-client build
WORKDIR /src
CMD tox --workdir /tmp/tox --recreate
