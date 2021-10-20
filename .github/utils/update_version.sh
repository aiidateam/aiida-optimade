#!/usr/bin/env bash
set -e

echo -e "\n### Setting commit user ###"
git config --local user.email "${GIT_USER_EMAIL}"
git config --local user.name "${GIT_USER_NAME}"

echo -e "\n### Update version ###"
invoke setver --version="${GITHUB_REF#refs/tags/}"

echo -e "\n### Commit updated files ###"
git add setup.json aiida_optimade/__init__.py aiida_optimade/config.json tests/static/test_config.json
git add CHANGELOG.md
git commit -m "Release ${GITHUB_REF#refs/tags/}"

echo -e "\n### Update tag ###"
TAG_MSG=.github/utils/release_tag_msg.txt
sed -i "s|TAG_NAME|${GITHUB_REF#refs/tags/}|g" "${TAG_MSG}"
git tag -af -F "${TAG_MSG}" ${GITHUB_REF#refs/tags/}
