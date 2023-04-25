#! /bin/sh -e

PUID=${PUID:-911}
PGID=${PGID:-911}

groupmod -o -g "$PGID" abc
usermod -o -u "$PUID" abc


mkdir -p /root/.ssh
ssh-keyscan -t rsa github.com >> /root/.ssh/known_hosts 2> /dev/null
if ! [ -z "$SSH_PRIVATE_KEY" ]; then
    echo "$SSH_PRIVATE_KEY" > /root/.ssh/id_rsa
fi

# Use exec to replace entrypoint with python3 as PID1
su-exec abc:$PGID python3 docker_appdatur/server.py "$@"
