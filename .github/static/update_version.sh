#!/usr/bin/env bash
set -e

echo -e "\n### Setting commit user ###"
git config --local user.email "casper.andersen@epfl.ch"
git config --local user.name "CasperWA"

echo -e "\n### Update version ###"
invoke setver --version="${GITHUB_REF#refs/tags/}"

echo -e "\n### Commit updated files ###"
git add setup.json
git add aiida_optimade/__init__.py
git add aiida_optimade/config.json
git add tests/static/test_config.json
git commit -m "Release ${GITHUB_REF#refs/tags/}"

echo -e "\n### Update tag ###"
TAG_MSG=.github/static/release_tag_msg.txt
sed -i "s|TAG_NAME|${GITHUB_REF#refs/tags/}|g" "${TAG_MSG}"
git tag -af -F "${TAG_MSG}" ${GITHUB_REF#refs/tags/}
