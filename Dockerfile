FROM docker as dind
ARG DOCKER_COMPOSE_VERSION=2.18.0

FROM python:3.11-alpine

COPY --from=docker:dind /usr/local/bin/docker /usr/local/bin/

RUN apk add --no-cache --update \
    bash \
    git \
    openssh \
    su-exec \
    shadow && \
    useradd -u 911 -U -d /config -s /bin/false abc && usermod -G users abc

RUN apk add --no-cache \
        curl \
        gcc \
        libressl-dev \
        musl-dev \
        libffi-dev && \
    pip3 install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
    DOCKER_CONFIG=/root/.docker && mkdir -p "${DOCKER_CONFIG}/cli-plugins" && \
    APK_ARCH=`apk --print-arch` && \
    DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-${APK_ARCH}" && \
    curl -SL "${DOCKER_COMPOSE_URL}" -o "${DOCKER_CONFIG}/cli-plugins/docker-compose" && \
    chmod +x "${DOCKER_CONFIG}/cli-plugins/docker-compose" && \
    apk del \
        curl \
        gcc \
        libressl-dev \
        musl-dev \
        libffi-dev


WORKDIR /usr/src/app
COPY pyproject.toml poetry.lock README.md docker_entrypoint.sh .
RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-root

# COPY docker_appdatur ./docker_appdatur
COPY docker_appdatur ./docker_appdatur

# Install again after copying files
RUN poetry install --without dev

ENV PORT=5000
ENV LISTEN_HOST=0.0.0.0
ENV DEBUG=docker-appdatur
ENV PYTHONUNBUFFERED=1

ENV REPO_URL=
ENV REPO_DEST=
ENV REPO_BOOTSTRAP=
ENV LOGLEVEL=info

EXPOSE 5000

ENTRYPOINT ["./docker_entrypoint.sh"]
CMD []
