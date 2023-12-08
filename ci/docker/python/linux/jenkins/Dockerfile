ARG PYTHON_VERSION=3.11
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_TRUSTED_HOST
ARG SONAR_SCANNER_VERSION=5.0.1.3006
ARG PIP_FIND_LINKS=/wheels/
FROM python:${PYTHON_VERSION} AS base_image

FROM base_image AS wheel_builder
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_TRUSTED_HOST
ARG PIP_FIND_LINKS

COPY requirements-dev.txt /requirements/
COPY requirements/ /requirements/requirements/

ARG PIP_FIND_LINKS
RUN mkdir -p ${PIP_FIND_LINKS} &&  \
    pip wheel --wheel-dir=${PIP_FIND_LINKS} --no-cache-dir -r /requirements/requirements-dev.txt
#==============================================================================
FROM base_image AS SONAR_BUILDER
RUN apt-get update && \
    apt-get install --no-install-recommends -y unzip

ARG SONAR_SCANNER_VERSION
ARG SONAR_SCANNER_HOME=/opt/sonar/${SONAR_SCANNER_VERSION}-linux
ENV SONAR_USER_HOME=/opt/sonar/.sonar
RUN curl --create-dirs -sSLo /tmp/sonar-scanner.zip \
        https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-$SONAR_SCANNER_VERSION-linux.zip && \
    unzip -o /tmp/sonar-scanner.zip -d /opt/sonar/ && \
    rm /tmp/sonar-scanner.zip && \
    mkdir -p $SONAR_USER_HOME/cache && \
    chmod -R 777 "${SONAR_USER_HOME}" &&\
    ln -s /opt/sonar/sonar-scanner-$SONAR_SCANNER_VERSION-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
    which sonar-scanner

FROM base_image
COPY --from=SONAR_BUILDER /opt/sonar /opt/sonar/
ARG SONAR_SCANNER_VERSION
ENV SONAR_SCANNER_VERSION=${SONAR_SCANNER_VERSION}
ARG SONAR_SCANNER_HOME=/opt/sonar/${SONAR_SCANNER_VERSION}-linux
ENV SONAR_USER_HOME=/opt/sonar/.sonar
RUN ln -s /opt/sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
    which sonar-scanner
RUN mkdir -p /home/user/.sonar/ && chmod -R 777 /home/user/

ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_TRUSTED_HOST
ARG PIP_FIND_LINKS

COPY --from=wheel_builder ${PIP_FIND_LINKS}/* ${PIP_FIND_LINKS}/
COPY --from=wheel_builder requirements/ /requirements

RUN pip install --no-index --no-cache-dir --find-links=${PIP_FIND_LINKS} \
    -r /requirements/requirements-dev.txt

ENV PIP_FIND_LINKS=${PIP_FIND_LINKS}
