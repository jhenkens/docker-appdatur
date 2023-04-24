FROM docker as dind


FROM python:3.11-alpine

COPY --from=docker:dind /usr/local/bin/docker /usr/local/bin/docker-compose /usr/local/bin/

RUN apk add --no-cache --update \
    bash \
    git \
    openssh


RUN apk add --no-cache \
        curl \
        gcc \
        libressl-dev \
        musl-dev \
        libffi-dev && \
    # curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile=minimal && \
    # source $HOME/.cargo/env && \
    pip3 install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
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
