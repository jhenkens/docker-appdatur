#! /bin/bash
set -e
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR/.."
docker build -t docker-appdatur .
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock -p 5000:5000 --name=docker-appdatur docker-appdatur
