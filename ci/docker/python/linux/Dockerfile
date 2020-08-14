ARG PYTHON_DOCKER_IMAGE_BASE="python:3.8"
FROM ${PYTHON_DOCKER_IMAGE_BASE} as wheel_builder
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_TRUSTED_HOST
ENV PIP_NO_CACHE_DIR=1
ADD requirements.txt ci/docker/python/shared/requirements-ci.txt ci/docker/python/shared/requirements-extra.txt /tmp/
RUN python -m pip install --upgrade pip &&  \
    pip install setuptools && \
    pip install wheel && \
    pip wheel --wheel-dir=/wheels  \
        -r /tmp/requirements.txt \
        -r /tmp/requirements-ci.txt && \
    pip wheel --wheel-dir=/wheels -r /tmp/requirements-extra.txt && \
    rm -rf  /root/.cache

FROM ${PYTHON_DOCKER_IMAGE_BASE}
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g $GROUP_ID user && \
    useradd -u $USER_ID -s /bin/sh -m -d /home/user -g user user

COPY --from=wheel_builder /wheels /wheels/
ADD requirements.txt ci/docker/python/shared/requirements-ci.txt /tmp/

RUN python -m pip install --upgrade pip && \
    pip install --no-index --find-links=/wheels \
        -r /tmp/requirements.txt \
        -r /tmp/requirements-ci.txt

USER user
WORKDIR /home/user