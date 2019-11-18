# aiida-optimade

Optimade API implementation for AiiDA

## Prerequisites

Environment where AiiDA is installed.

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
