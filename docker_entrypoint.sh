#! /bin/sh -e

PUID=${PUID:-911}
PGID=${PGID:-911}

groupmod -o -g "$PGID" abc
usermod -o -u "$PUID" abc

mkdir -p /config/.docker
chown abc:$PGID /config
chown abc:$PGID /config/.docker

SSH_CONFIG="/config/.ssh"
SSH_KNOWN_HOSTS="$SSH_CONFIG/known_hosts"

if ! [ -f "$SSH_KNOWN_HOSTS" ]; then
    mkdir -p "$SSH_CONFIG"
    ssh-keyscan -t rsa github.com >> "$SSH_KNOWN_HOSTS" 2> /dev/null
    chmod 600 "$SSH_KNOWN_HOSTS"
    chmod 700 "$SSH_CONFIG"
    chown abc:$PGID "$SSH_KNOWN_HOSTS"
    chown abc:$PGID "$SSH_CONFIG"
fi

# Use exec to replace entrypoint with python3 as PID1
su-exec abc:$PGID python3 docker_appdatur/server.py "$@"
