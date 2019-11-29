# Optimade API implementation for AiiDA

This is a RESTful API server created with [FastAPI](https://fastapi.tiangolo.com/) that exposes an AiiDA database according to the [OPTiMaDe specification](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.rst).

The server is based on the test server "template" used in the [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools) package.
Indeed, the filter grammar and parser and [`pydantic`](https://5d584fcca7c9b70007d1c997--pydantic-docs.netlify.com/) models from [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools) are used directly here.

Lastly, the server utilizes the FastAPI concept of [routers](https://fastapi.tiangolo.com/tutorial/bigger-applications/#apirouter), which means each endpoint can be "setup" several times, allowing multiple base URLs and more flexibility.

## Prerequisites

Environment where AiiDA is installed.  
AiiDA database containing `StructureData` nodes, since these are the _only_ AiiDA nodes that are currently exposed with this API (under the `/structures` endpoint).

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
# specify AiiDA profile (will use default otherwise)
export AIIDA_PROFILE=optimade
sh run.sh
```

Navigate to `http://127.0.0.1:5000/optimade/info`

## Running via docker

Adapt `profiles/quicksetup.json` and `profiles/docker-compose.yml` appropriately.

```shell
docker-compose -f profiles/docker-compose.yml up --build
```

Navigate to `http://127.0.0.1:3253/optimade/info`

Stop by using

```shell
docker-compose -f profiles/docker-compose.yml down
```

## Design choices

**Q: Why create an individual `config.json` file instead of just mounting an existing `.aiida` directory and using that directly?**  
**A:** This, currently, wouldn't work because the `REPOSITORY_URI` needs to point to the right path *inside* the container, not on the host. Furthermore, storing all configurations in the same file can be fragile.
