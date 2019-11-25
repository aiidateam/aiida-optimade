# Optimade API implementation for AiiDA

This is a server using [FastAPI](https://fastapi.tiangolo.com/) that exposes an AiiDA database according to the [OPTiMaDe specification](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.rst).

The server is based on the test server "template" used in [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools).
Indeed, the filter grammar and parser and [`pydantic`](https://5d584fcca7c9b70007d1c997--pydantic-docs.netlify.com/) models from `optimade-python-tools` are used directly here.

Lastly, the server utilizes the FastAPI concept of [routers](https://fastapi.tiangolo.com/tutorial/bigger-applications/#apirouter), which means each endpoint can be "setup" several times, allowing multiple base URLs and more flexibility.

## Prerequisites

Environment where AiiDA is installed.

> **Note**: At the moment, `aiida-optimade` works most optimally with an AiiDA database using the SQLAlchemy backend.

## Installation

```shell
git clone https://github.com/Materials-Consortia/optimade-python-tools
pip install -e optimade-python-tools/
git clone https://github.com/aiidateam/aiida-optimade
pip install -e aiida-optimade/
```

## Running the server locally

```shell
# specify profile (will take default otherwise)
export AIIDA_PROFILE=optimade
sh run.sh
```

Navigate to `http://127.0.0.1:5000/info`

## Running via docker

Adapt `docker-compose.yml` and `.docker/config.json` appropriately.

```shell
docker-compose up --build
```

Navigate to `http://127.0.0.1:3253/info`
