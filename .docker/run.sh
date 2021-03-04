#!/usr/bin/env bash
set -ex

mkdir -p ${AIIDA_PATH}/.aiida
cp -n /profiles/${AIIDA_PROFILE}.json ${AIIDA_PATH}/.aiida/config.json

# make docker.host.internal available
# see https://github.com/docker/for-linux/issues/264#issuecomment-387525409
# ltalirz: Only works for Mac, not Linux
# echo -e "`/sbin/ip route|awk '/default/ { print $3 }'`\tdocker.host.internal" | tee -a /etc/hosts > /dev/null

if [ -n "${MONGO_FILENAME}" ]; then
    for line in $(ls -1 /app/.mongo); do
        if [ "${line}" == "${MONGO_FILENAME}" ]; then
            load_mongo_file="--filename /app/.mongo/${MONGO_FILENAME}"
            break
        fi
    done
fi

# Initialize database
aiida-optimade --profile ${AIIDA_PROFILE} init ${FORCE_INIT} ${USE_MONGO} ${load_mongo_file}

# Run (uvicorn) server
aiida-optimade --profile ${AIIDA_PROFILE} run --host 0.0.0.0 --port 80
