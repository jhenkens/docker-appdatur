FROM docker as dind


FROM python:3.11-alpine

COPY --from=docker:dind /usr/local/bin/docker /usr/local/bin/docker-compose /usr/local/bin/

RUN apk add --no-cache --update \
    git

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
COPY pyproject.toml poetry.lock README.md .
RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-root

COPY docker_appdatur ./docker_appdatur

# Install again after copying files
RUN poetry install --without dev

ENV PORT=5000
ENV LISTEN_HOST=0.0.0.0
ENV DEBUG=docker-appdatur

EXPOSE 5000

ENTRYPOINT ["python3", "docker_appdatur/server.py"]
CMD []
