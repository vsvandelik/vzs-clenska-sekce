#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
python "${SCRIPTPATH}/manage.py" dumpdata --exclude=auth --exclude=contenttypes > "${SCRIPTPATH}/data/db.json"
