# Optimade API implementation for AiiDA

| Latest release | Build status | Activity |
|:--------------:|:------------:|:--------:|
| [![PyPI](https://img.shields.io/pypi/v/aiida-optimade)](https://pypi.org/project/aiida-optimade/)<br>[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aiida-optimade)](https://pypi.org/project/aiida-optimade/)<br>[![OPTiMaDe](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/v0.3.2/.ci/optimade-version.json)](https://github.com/Materials-Consortia/OPTiMaDe/) | [![GitHub Workflow Status](https://img.shields.io/github/workflow/status/aiidateam/aiida-optimade/aiida-optimade)](https://github.com/aiidateam/aiida-optimade/actions/)<br>[![Codecov](https://img.shields.io/codecov/c/gh/aiidateam/aiida-optimade)](https://codecov.io/gh/aiidateam/aiida-optimade) | [![GitHub last commit](https://img.shields.io/github/last-commit/aiidateam/aiida-optimade)](https://github.com/aiidateam/aiida-optimade) |

This is a RESTful API server created with [FastAPI](https://fastapi.tiangolo.com/) that exposes an AiiDA database according to the [OPTiMaDe specification](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.rst).

It is mainly used by [Materials Cloud](https://www.materialscloud.org/) to expose access to archived AiiDA databases through the OPTiMaDe API.
But it may be freely implemented by any to fulfill a similar purpose.

The server is based on the test server "template" used in the [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools) package.
Indeed, the filter grammar and parser and [`pydantic`](https://5d584fcca7c9b70007d1c997--pydantic-docs.netlify.com/) models from [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools) are used directly here.

Lastly, the server utilizes the FastAPI concept of [routers](https://fastapi.tiangolo.com/tutorial/bigger-applications/#apirouter), which means each endpoint can be "setup" several times, allowing multiple base URLs and more flexibility.

## Prerequisites

Environment where AiiDA is installed.  
AiiDA database containing `StructureData` nodes, since these are the _only_ AiiDA nodes that are currently exposed with this API (under the `/structures` endpoint).

## Installation

```shell
git clone https://github.com/Materials-Consortia/optimade-python-tools
pip install -e optimade-python-tools/
git clone https://github.com/aiidateam/aiida-optimade
pip install -e aiida-optimade/
```

## Running the server locally

```shell
# specify AiiDA profile (will use default otherwise)
export AIIDA_PROFILE=optimade
./aiida-optimade/run.sh
```

Navigate to `http://localhost:5000/optimade/info`

## Running via docker

Adapt `profiles/quicksetup.json` and `profiles/docker-compose.yml` appropriately.

```shell
docker-compose -f profiles/docker-compose.yml up --build
```

Navigate to `http://localhost:3253/optimade/info`

Stop by using

```shell
docker-compose -f profiles/docker-compose.yml down
```

## Design choices

**Q: Why create an individual `config.json` file instead of just mounting an existing `.aiida` directory and using that directly?**  
**A:** This, currently, wouldn't work because the `REPOSITORY_URI` needs to point to the right path *inside* the container, not on the host. Furthermore, storing all configurations in the same file can be fragile.
