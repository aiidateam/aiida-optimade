# aiida-optimade
Optimade API implementation for AiiDA

## Prerequisites
Environment where AiiDA is installed.

## Installation
```
pip install -e .
git clone https://github.com/Materials-Consortia/optimade-python-tools
pip install optimade-tools
```

## Running the server locally

```
# specify profile (will take default otherwise)
export AIIDA_PROFILE=quicksetup
./run.sh
```
Navigate to `http://127.0.0.1:5000/info`

## Running via docker

Adapt `docker-compose.yml` and `.docker/config.json` appropriately.
```
docker-compose up --build
```
Navigate to `http://127.0.0.1:3253/info`

