#!/bin/bash

LOG_LEVEL=info

if [ "$1" = "debug" ]; then
    export OPTIMADE_DEBUG=1
    LOG_LEVEL=debug
    if [ -n "$2" ]; then
        export AIIDA_PROFILE=$2
    else
        export AIIDA_PROFILE="optimade_sqla"
    fi
elif [ -n "$1" ]; then
    export AIIDA_PROFILE=$1
    if [ "$2" = "debug" ]; then
        export OPTIMADE_DEBUG=1
        LOG_LEVEL=debug
    fi
else
    export AIIDA_PROFILE="optimade_sqla"
fi

uvicorn --reload --port 5000 --log-level ${LOG_LEVEL} aiida_optimade.main:APP
