#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
docker build -t vzs-clenska-sekce "$SCRIPTPATH"
