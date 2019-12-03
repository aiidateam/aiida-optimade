#!/usr/bin/env bash
set -ev

CODECOV_FILE=.codecov.yml

curl -s --data-binary @${CODECOV_FILE} https://codecov.io/validate | grep Valid! || ( curl -s --data-binary @${CODECOV_FILE} https://codecov.io/validate ; exit 1)
