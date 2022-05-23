# OPTIMADE API implementation for AiiDA

| Latest release | Build status | Activity |
|:--------------:|:------------:|:--------:|
| [![AiiDA](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/aiidateam/aiida-optimade/develop/.ci/aiida-version.json)](https://github.com/aiidateam/aiida-core/)<br>[![PyPI](https://img.shields.io/pypi/v/aiida-optimade)](https://pypi.org/project/aiida-optimade/)<br>[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aiida-optimade)](https://pypi.org/project/aiida-optimade/)<br>[![OPTIMADE](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/v0.17.2/optimade-version.json)](https://github.com/Materials-Consortia/OPTIMADE/) | [![GitHub Workflow Status](https://img.shields.io/github/workflow/status/aiidateam/aiida-optimade/aiida-optimade)](https://github.com/aiidateam/aiida-optimade/actions/)<br>[![Codecov](https://img.shields.io/codecov/c/gh/aiidateam/aiida-optimade)](https://codecov.io/gh/aiidateam/aiida-optimade) | [![GitHub last commit](https://img.shields.io/github/last-commit/aiidateam/aiida-optimade)](https://github.com/aiidateam/aiida-optimade) |

This is a RESTful API server created with [FastAPI](https://fastapi.tiangolo.com/) that exposes an AiiDA database according to the [OPTIMADE specification](https://github.com/Materials-Consortia/OPTIMADE/blob/develop/optimade.rst).

It is mainly used by [Materials Cloud](https://www.materialscloud.org/) to expose access to archived AiiDA databases through the OPTIMADE API.
But it may be freely implemented by any to fulfill a similar purpose.

The server is based on the test server "template" used in the [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools) package.
Indeed, the filter grammar and parser and [`pydantic`](https://pydantic-docs.helpmanual.io/) models from [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools) are used directly here.

## Prerequisites

Environment where AiiDA is installed.  
AiiDA database containing `StructureData` nodes, since these are the _only_ AiiDA nodes that are currently exposed with this API (under the `/structures` endpoint).

## Installation

The package is relased on PyPI, hence you can install it by:

```shell
$ pip install aiida-optimade
```

Otherwise, you can also `git clone` the repository from GitHub:

```shell
$ git clone https://github.com/aiidateam/aiida-optimade /path/to/aiida-optimade/parent/dir
$ pip install -e /path/to/aiida-optimade
```

### Development

For developers, there is a special setuptools extra `dev`, which can be installed by:

```shell
$ pip install aiida-optimade[dev]
```

or

```shell
$ pip install -e /path/to/aiida-optimade[dev]
```

This package uses [Black](https://black.readthedocs.io/en/stable/) for formatting.
If you wish to contribute, please install the git pre-commit hook:

```shell
/path/to/aiida-optimade$ pre-commit install
```

This will automatically update the formatting when running `git commit`, as well as check the validity of various repository JSON and YAML files.

For testing run `pytest`, which will run with an AiiDA backend as standard.
The tests can also be run with the MongoDB backend by setting the environment variable `PYTEST_OPTIMADE_CONFIG_FILE`, the value being a path to the config file to be used:

```shell
$ PYTEST_OPTIMADE_CONFIG_FILE=/path/to/aiida-optimade/tests/static/test_mongo_config.json pytest
```

However, note that the `mongo_uri` value will have to be updated according to your local setup.

## Initialization

You should first initialize your AiiDA profile.

This can be done by using the `aiida-optimade` CLI:

```shell
$ aiida-optimade -p <PROFILE> init
```

Where `<PROFILE>` is the AiiDA profile.

> **Note**: Currently, the default is `optimade`, if the `-p / --profile` option is now specified.
> This will be changed in the future to use the default AiiDA profile.

Initialization goes through your profile's `StructureData` nodes, adding an `optimade` extra, wherein all OPTIMADE-specific fields that do not have an equivalent AiiDA property are stored.

If in the future, more `StructureData` nodes are added to your profile's database, these will be automatically updated for the first query, filtering on any of these OPTIMADE-specific fields.
However, if you do not wish a significant lag for the user or risking several GET requests coming in at the same time, trying to update your profile's database, you should re-run `aiida-optimade init` for your profile (in between shutting the server down and restarting it again).

## Running the server

### Locally

Using the `aiida-optimade` CLI, you can do the following:

```shell
$ aiida-optimade -p <PROFILE> run
```

Where `<PROFILE>` is the AiiDA profile you wish to serve.

> **Note**: Currently, the default is `optimade`, if the `-p / --profile` option is now specified.
> This will be changed in the future to use the default AiiDA profile.

You also have the opportunity to specify the AiiDA profile via the environment variable `AIIDA_PROFILE`.
Note, however, that if a profile name is passed to the CLI, it will overrule _and replace_ the current `AIIDA_PROFILE` environment variable.

```shell
# Specifying AiiDA profile as an environment variable
$ export AIIDA_PROFILE=optimade
$ aiida-optimade run
```

Navigate to `http://localhost:5000/v1/info`

> **Tip**: To see the default AiiDA profile, type `verdi profile list` to find the colored profile name marked with an asterisk (`*`), or type `verdi profile show`, which will show you more detailed information about the default profile.

> **Note**: The `aiida-optimade run` command has more options to configure your server, run
>
> ```shell
> $ aiida-optimade run --help
> ```
>
> for more information.

### With Docker

Adapt `profiles/test_django.json` and `profiles/docker-compose.yml` appropriately.

```shell
$ docker-compose -f profiles/docker-compose.yml up --build
```

Navigate to `http://localhost:3253/v1/info`

Stop by using

```shell
$ docker-compose -f profiles/docker-compose.yml down
```

#### Jinja templates

If you are familiar with [Jinja](https://palletsprojects.com/p/jinja/), there are two templates to create the JSON and YAML files: `profiles/config.j2` and `profiles/docker-compose.j2`, respectively.

## Configure the server

You can configure the server with the `aiida_optimade/config.json` file or set certain environment variables.

To learn more about this, see the [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools) repository.

## Design choices

**Q: Why create an individual `config.json` file instead of just mounting an existing `.aiida` directory and using that directly?**  
**A:** This, currently, wouldn't work because the `REPOSITORY_URI` needs to point to the right path *inside* the container, not on the host. Furthermore, storing all configurations in the same file can be fragile.
