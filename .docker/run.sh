#!/bin/bash
set -ex
mkdir -p $AIIDA_PATH/.aiida
cp /profiles/$AIIDA_PROFILE.json $AIIDA_PATH/.aiida/config.json
uvicorn aiida_optimade.main:app --host 0.0.0.0 --port 80
