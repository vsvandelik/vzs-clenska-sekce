#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
python "${SCRIPTPATH}/manage.py" loaddata "${SCRIPTPATH}/data/db.json"
