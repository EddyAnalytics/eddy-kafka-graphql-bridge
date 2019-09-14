#!/bin/sh
set -e

if [ "$1" = 'eddy-kafka-graphql-bridge' ]; then
    exec uvicorn --host 0.0.0.0 --reload app:app
fi

exec "$@"
