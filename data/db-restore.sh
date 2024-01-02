#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT")
PROJECT_DIR=$(dirname "$SCRIPT_DIR")
python "${PROJECT_DIR}/manage.py" loaddata "${SCRIPT_DIR}/db.json"
