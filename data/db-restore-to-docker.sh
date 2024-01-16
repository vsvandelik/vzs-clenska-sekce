#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT")
docker cp "${SCRIPT_DIR}/db.json" vzs-clenska-sekce-backend:/usr/src/app/data/db.json
docker exec vzs-clenska-sekce-backend sh -c 'chmod +x /usr/src/app/data/db-restore.sh'
docker exec vzs-clenska-sekce-backend sh -c '/usr/src/app/data/db-restore.sh'
