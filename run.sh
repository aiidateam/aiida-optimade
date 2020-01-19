#!/bin/bash
if [ -n "$1" ]
then
    export AIIDA_PROFILE=$1
else
    export AIIDA_PROFILE="optimade_sqla"
fi

uvicorn aiida_optimade.main:APP --reload --port 5000
