#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT")
DOCKERFILE="$SCRIPT_DIR/Dockerfile"
PROJECT_DIR=$(dirname "$SCRIPT_DIR")
docker build -t vzs-clenska-sekce "$PROJECT_DIR" -f "$DOCKERFILE"
