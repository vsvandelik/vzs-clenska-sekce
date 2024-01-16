#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT")
docker exec vzs-clenska-sekce-backend sh -c 'chmod +x /usr/src/app/data/db-backup.sh'
docker exec vzs-clenska-sekce-backend sh -c '/usr/src/app/data/db-backup.sh'
docker cp vzs-clenska-sekce-backend:/usr/src/app/data/db.json "${SCRIPT_DIR}/db.json"
