#!/bin/sh
set -e

echo "\n### Checkout fresh branch ###"
git checkout -b update_version

echo "\n### Setting commit user ###"
git config --local user.email "casper.andersen@epfl.ch"
git config --local user.name "CasperWA"

echo "\n### Install invoke ###"
pip install -U invoke

echo "\n### Update version ###"
invoke setver --version="${GITHUB_REF#refs/tags/}"

echo "\n### Commit updated files ###"
git add setup.json
git add aiida_optimade/__init__.py
git add aiida_optimade/config.json
git add tests/static/test_config.json
git commit -m "Release ${GITHUB_REF#refs/tags/}"
