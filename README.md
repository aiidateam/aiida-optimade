# OPTIMADE API implementation for AiiDA

The compatibility matrix below assumes the user always install the latest patch release of the specified minor version, which is recommended.

| Plugin | AiiDA | Python | Specification |
|-|-|-|-|
| `v1.2 < v2.0` | ![Compatibility for v1.0][AiiDA v2 py311 range] |  [![PyPI pyversions](https://img.shields.io/pypi/pyversions/aiida-optimade)](https://pypi.org/project/aiida-optimade) | ![OPTIMADE API compatibility][OPTIMADE from OPT] |
| `v1.0 < v1.2` | ![Compatibility for v1.0][AiiDA v2 py38 range] |  [![PyPI pyversions][Python v3.8-v3.10]](https://pypi.org/project/aiida-optimade/1.1.1/) | ![OPTIMADE API compatibility][OPTIMADE from OPT] |
| `v0.18 <= v0.20` | ![Compatibility for v0][AiiDA v1 range] |  [![PyPI pyversions][Python v3.7-v3.9]](https://pypi.org/project/aiida-optimade/0.20.0/) | ![OPTIMADE API compatibility][OPTIMADE from OPT] |

| Latest release | Build status | Activity |
|:--------------:|:------------:|:--------:|
| [![AiiDA](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/aiidateam/aiida-optimade/develop/.ci/aiida-version.json)](https://github.com/aiidateam/aiida-core/)<br>[![PyPI](https://img.shields.io/pypi/v/aiida-optimade)](https://pypi.org/project/aiida-optimade/)<br>[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aiida-optimade)](https://pypi.org/project/aiida-optimade/)<br>[![OPTIMADE](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/v0.25.3/optimade-version.json)](https://github.com/Materials-Consortia/OPTIMADE/) | [![GitHub Workflow Status](https://img.shields.io/github/workflow/status/aiidateam/aiida-optimade/aiida-optimade)](https://github.com/aiidateam/aiida-optimade/actions/)<br>[![Codecov](https://img.shields.io/codecov/c/gh/aiidateam/aiida-optimade)](https://codecov.io/gh/aiidateam/aiida-optimade) | [![GitHub last commit](https://img.shields.io/github/last-commit/aiidateam/aiida-optimade)](https://github.com/aiidateam/aiida-optimade) |

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

> **Note**: Currently, the default is `optimade`, if the `-p / --profile` option is not specified.
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

Adapt `profiles/test_psql_dos.json` and `profiles/docker-compose.yml` appropriately.

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

### Using AiiDA group for curated data

An [AiiDA Group](https://aiida.readthedocs.io/projects/aiida-core/en/latest/howto/data.html#organizing-data) can be used to curate data and serve only this curated data through the OPTIMADE server.
Setting the `query_group` option in `config.json` will ensure only the valid (`StructureData`, `CifData`) data nodes in the given AiiDA Group will be served.
Set the `query_group` parameter to `null` (default) to serve all structure data from the database.

## Design choices

**Q: Why create an individual `config.json` file instead of just mounting an existing `.aiida` directory and using that directly?**  
**A:** This, currently, wouldn't work because the `REPOSITORY_URI` needs to point to the right path *inside* the container, not on the host. Furthermore, storing all configurations in the same file can be fragile.

## For maintainers

To release the new version, go to GitHub release API of the repo create a new release and update the release information.  
The release action will be triggered by newly created release.
Note, the tag should start with a `v` and be followed by a full semantic version (see [SemVer](https://semver.org)).
For example: `v2.3.12`.

[AiiDA v2 py311 range]: https://img.shields.io/badge/AiiDA->=2.2.0,<3.0.0-007ec6.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACMAAAAhCAYAAABTERJSAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAFhgAABYYBG6Yz4AAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAUbSURBVFiFzZhrbFRVEMd%2Fc%2B5uu6UUbIFC%2FUAUVEQCLbQJBIiBDyiImJiIhmohYNCkqJAQxASLF8tDgYRHBLXRhIcKNtFEhVDgAxBJqgmVh4JEKg3EIn2QYqBlt917xg%2BFss%2ByaDHOtzsz5z%2B%2FuZl7ztmF%2F5HJvxVQN6cPYX8%2FPLnOmsvNAvqfwuib%2FbNIk9cQeQnLcKRL5xLIV%2Fic9eJeunjPYbRs4FjQSpTB3aS1IpRKeeOOewajy%2FKKEO8Q0DuVdKy8IqsbPulxGHUfCBBu%2BwUYGuFuBTK7wQnht6PEbf4tlRomVRjCbXNjQEB0AyrFQOL5ENIJm7dTLZE6DPJCnEtFZVXDLny%2B4Sjv0PmmYu1ZdUek9RiMgoDmJ8V0L7XJqsZ3UW8YsBOwEeHeeFce7jEYXBy0m9m4BbXqSj2%2Bxnkg26MCVrN6DEZcwggtd8pTFx%2Fh3B9B50YLaFOPwXQKUt0tBLegtSomfBlfY13PwijbEnhztGzgJsK5h9W9qeWwBqjvyhB2iBs1Qz0AU974DciRGO8CVN8AJhAeMAdA3KbrKEtvxhsI%2B9emWiJlGBEU680Cfk%2BSsVqXZvcFYGXjF8ABVJ%2BTNfVXehyms1zzn1gmIOxLEB6E31%2FWBe5rnCarmo7elf7dJEeaLh80GasliI5F6Q9cAz1GY1OJVNDxTzQTw7iY%2FHEZRQY7xqJ9RU2LFe%2FYqakdP911ha0XhjjiTVAkDwgatWfCGeYocx8M3glG8g8EXhSrLrHnEFJ5Ymow%2FkhIYv6ttYUW1iFmEqqxdVoUs9FmsDYSqmtmJh3Cl1%2BVtl2s7owDUdocR5bceiyoSivGTT5vzpbzL1uoBpmcAAQgW7ArnKD9ng9rc%2BNgrobSNwpSkkhcRN%2BvmXLjIsDovYHHEfmsYFygPAnIDEQrQPzJYCOaLHLUfIt7Oq0LJn9fxkSgNCb1qEIQ5UKgT%2Fs6gJmVOOroJhQBXVqw118QtWLdyUxEP45sUpSzqP7RDdFYMyB9UReMiF1MzPwoUqHt8hjGFFeP5wZAbZ%2F0%2BcAtAAcji6LeSq%2FMYiAvSsdw3GtrfVSVFUBbIhwRWYR7yOcr%2FBi%2FB1MSJZ16JlgH1AGM3EO2QnmMyrSbTSiACgFBv4yCUapZkt9qwWVL7aeOyHvArJjm8%2Fz9BhdI4XcZgz2%2FvRALosjsk1ODOyMcJn9%2FYI6IrkS5vxMGdUwou2YKfyVqJpn5t9aNs3gbQMbdbkxnGdsr4bTHm2AxWo9yNZK4PXR3uzhAh%2BM0AZejnCrGdy0UvJxl0oMKgWSLR%2B1LH2aE9ViejiFs%2BXn6bTjng3MlIhJ1I1TkuLdg6OcAbD7Xx%2Bc3y9TrWAiSHqVkbZ2v9ilCo6s4AjwZCzFyD9mOL305nV9aonvsQeT2L0gVk4OwOJqXXVRW7naaxswDKVdlYLyMXAnntteYmws2xcVVZzq%2BtHPAooQggmJkc6TLSusOiL4RKgwzzYU1iFQgiUBA1H7E8yPau%2BZl9P7AblVNebtHqTgxLfRqrNvZWjsHZFuqMqKcDWdlFjF7UGvX8Jn24DyEAykJwNcdg0OvJ4p5pQ9tV6SMlP4A0PNh8aYze1ArROyUNTNouy8tNF3Rt0CSXb6bRFl4%2FIfQzNMjaE9WwpYOWQnOdEF%2BTdJNO0iFh7%2BI0kfORzQZb6P2kymS9oTxzBiM9rUqLWr1WE5G6ODhycQd%2FUnNVeMbcH68hYkGycNoUNWc8fxaxfwhDbHpfwM5oeTY7rUX8QAAAABJRU5ErkJggg%3D%3D

[AiiDA v2 py38 range]: https://img.shields.io/badge/AiiDA->=2.0.0,<2.4.0-007ec6.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACMAAAAhCAYAAABTERJSAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAFhgAABYYBG6Yz4AAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAUbSURBVFiFzZhrbFRVEMd%2Fc%2B5uu6UUbIFC%2FUAUVEQCLbQJBIiBDyiImJiIhmohYNCkqJAQxASLF8tDgYRHBLXRhIcKNtFEhVDgAxBJqgmVh4JEKg3EIn2QYqBlt917xg%2BFss%2ByaDHOtzsz5z%2B%2FuZl7ztmF%2F5HJvxVQN6cPYX8%2FPLnOmsvNAvqfwuib%2FbNIk9cQeQnLcKRL5xLIV%2Fic9eJeunjPYbRs4FjQSpTB3aS1IpRKeeOOewajy%2FKKEO8Q0DuVdKy8IqsbPulxGHUfCBBu%2BwUYGuFuBTK7wQnht6PEbf4tlRomVRjCbXNjQEB0AyrFQOL5ENIJm7dTLZE6DPJCnEtFZVXDLny%2B4Sjv0PmmYu1ZdUek9RiMgoDmJ8V0L7XJqsZ3UW8YsBOwEeHeeFce7jEYXBy0m9m4BbXqSj2%2Bxnkg26MCVrN6DEZcwggtd8pTFx%2Fh3B9B50YLaFOPwXQKUt0tBLegtSomfBlfY13PwijbEnhztGzgJsK5h9W9qeWwBqjvyhB2iBs1Qz0AU974DciRGO8CVN8AJhAeMAdA3KbrKEtvxhsI%2B9emWiJlGBEU680Cfk%2BSsVqXZvcFYGXjF8ABVJ%2BTNfVXehyms1zzn1gmIOxLEB6E31%2FWBe5rnCarmo7elf7dJEeaLh80GasliI5F6Q9cAz1GY1OJVNDxTzQTw7iY%2FHEZRQY7xqJ9RU2LFe%2FYqakdP911ha0XhjjiTVAkDwgatWfCGeYocx8M3glG8g8EXhSrLrHnEFJ5Ymow%2FkhIYv6ttYUW1iFmEqqxdVoUs9FmsDYSqmtmJh3Cl1%2BVtl2s7owDUdocR5bceiyoSivGTT5vzpbzL1uoBpmcAAQgW7ArnKD9ng9rc%2BNgrobSNwpSkkhcRN%2BvmXLjIsDovYHHEfmsYFygPAnIDEQrQPzJYCOaLHLUfIt7Oq0LJn9fxkSgNCb1qEIQ5UKgT%2Fs6gJmVOOroJhQBXVqw118QtWLdyUxEP45sUpSzqP7RDdFYMyB9UReMiF1MzPwoUqHt8hjGFFeP5wZAbZ%2F0%2BcAtAAcji6LeSq%2FMYiAvSsdw3GtrfVSVFUBbIhwRWYR7yOcr%2FBi%2FB1MSJZ16JlgH1AGM3EO2QnmMyrSbTSiACgFBv4yCUapZkt9qwWVL7aeOyHvArJjm8%2Fz9BhdI4XcZgz2%2FvRALosjsk1ODOyMcJn9%2FYI6IrkS5vxMGdUwou2YKfyVqJpn5t9aNs3gbQMbdbkxnGdsr4bTHm2AxWo9yNZK4PXR3uzhAh%2BM0AZejnCrGdy0UvJxl0oMKgWSLR%2B1LH2aE9ViejiFs%2BXn6bTjng3MlIhJ1I1TkuLdg6OcAbD7Xx%2Bc3y9TrWAiSHqVkbZ2v9ilCo6s4AjwZCzFyD9mOL305nV9aonvsQeT2L0gVk4OwOJqXXVRW7naaxswDKVdlYLyMXAnntteYmws2xcVVZzq%2BtHPAooQggmJkc6TLSusOiL4RKgwzzYU1iFQgiUBA1H7E8yPau%2BZl9P7AblVNebtHqTgxLfRqrNvZWjsHZFuqMqKcDWdlFjF7UGvX8Jn24DyEAykJwNcdg0OvJ4p5pQ9tV6SMlP4A0PNh8aYze1ArROyUNTNouy8tNF3Rt0CSXb6bRFl4%2FIfQzNMjaE9WwpYOWQnOdEF%2BTdJNO0iFh7%2BI0kfORzQZb6P2kymS9oTxzBiM9rUqLWr1WE5G6ODhycQd%2FUnNVeMbcH68hYkGycNoUNWc8fxaxfwhDbHpfwM5oeTY7rUX8QAAAABJRU5ErkJggg%3D%3D

[AiiDA v1 range]: https://img.shields.io/badge/AiiDA->=1.6.0,<2.0.0-007ec6.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACMAAAAhCAYAAABTERJSAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAFhgAABYYBG6Yz4AAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAUbSURBVFiFzZhrbFRVEMd%2Fc%2B5uu6UUbIFC%2FUAUVEQCLbQJBIiBDyiImJiIhmohYNCkqJAQxASLF8tDgYRHBLXRhIcKNtFEhVDgAxBJqgmVh4JEKg3EIn2QYqBlt917xg%2BFss%2ByaDHOtzsz5z%2B%2FuZl7ztmF%2F5HJvxVQN6cPYX8%2FPLnOmsvNAvqfwuib%2FbNIk9cQeQnLcKRL5xLIV%2Fic9eJeunjPYbRs4FjQSpTB3aS1IpRKeeOOewajy%2FKKEO8Q0DuVdKy8IqsbPulxGHUfCBBu%2BwUYGuFuBTK7wQnht6PEbf4tlRomVRjCbXNjQEB0AyrFQOL5ENIJm7dTLZE6DPJCnEtFZVXDLny%2B4Sjv0PmmYu1ZdUek9RiMgoDmJ8V0L7XJqsZ3UW8YsBOwEeHeeFce7jEYXBy0m9m4BbXqSj2%2Bxnkg26MCVrN6DEZcwggtd8pTFx%2Fh3B9B50YLaFOPwXQKUt0tBLegtSomfBlfY13PwijbEnhztGzgJsK5h9W9qeWwBqjvyhB2iBs1Qz0AU974DciRGO8CVN8AJhAeMAdA3KbrKEtvxhsI%2B9emWiJlGBEU680Cfk%2BSsVqXZvcFYGXjF8ABVJ%2BTNfVXehyms1zzn1gmIOxLEB6E31%2FWBe5rnCarmo7elf7dJEeaLh80GasliI5F6Q9cAz1GY1OJVNDxTzQTw7iY%2FHEZRQY7xqJ9RU2LFe%2FYqakdP911ha0XhjjiTVAkDwgatWfCGeYocx8M3glG8g8EXhSrLrHnEFJ5Ymow%2FkhIYv6ttYUW1iFmEqqxdVoUs9FmsDYSqmtmJh3Cl1%2BVtl2s7owDUdocR5bceiyoSivGTT5vzpbzL1uoBpmcAAQgW7ArnKD9ng9rc%2BNgrobSNwpSkkhcRN%2BvmXLjIsDovYHHEfmsYFygPAnIDEQrQPzJYCOaLHLUfIt7Oq0LJn9fxkSgNCb1qEIQ5UKgT%2Fs6gJmVOOroJhQBXVqw118QtWLdyUxEP45sUpSzqP7RDdFYMyB9UReMiF1MzPwoUqHt8hjGFFeP5wZAbZ%2F0%2BcAtAAcji6LeSq%2FMYiAvSsdw3GtrfVSVFUBbIhwRWYR7yOcr%2FBi%2FB1MSJZ16JlgH1AGM3EO2QnmMyrSbTSiACgFBv4yCUapZkt9qwWVL7aeOyHvArJjm8%2Fz9BhdI4XcZgz2%2FvRALosjsk1ODOyMcJn9%2FYI6IrkS5vxMGdUwou2YKfyVqJpn5t9aNs3gbQMbdbkxnGdsr4bTHm2AxWo9yNZK4PXR3uzhAh%2BM0AZejnCrGdy0UvJxl0oMKgWSLR%2B1LH2aE9ViejiFs%2BXn6bTjng3MlIhJ1I1TkuLdg6OcAbD7Xx%2Bc3y9TrWAiSHqVkbZ2v9ilCo6s4AjwZCzFyD9mOL305nV9aonvsQeT2L0gVk4OwOJqXXVRW7naaxswDKVdlYLyMXAnntteYmws2xcVVZzq%2BtHPAooQggmJkc6TLSusOiL4RKgwzzYU1iFQgiUBA1H7E8yPau%2BZl9P7AblVNebtHqTgxLfRqrNvZWjsHZFuqMqKcDWdlFjF7UGvX8Jn24DyEAykJwNcdg0OvJ4p5pQ9tV6SMlP4A0PNh8aYze1ArROyUNTNouy8tNF3Rt0CSXb6bRFl4%2FIfQzNMjaE9WwpYOWQnOdEF%2BTdJNO0iFh7%2BI0kfORzQZb6P2kymS9oTxzBiM9rUqLWr1WE5G6ODhycQd%2FUnNVeMbcH68hYkGycNoUNWc8fxaxfwhDbHpfwM5oeTY7rUX8QAAAABJRU5ErkJggg%3D%3D


[Python v3.8-v3.10]: https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue

[Python v3.7-v3.9]: https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue

[OPTIMADE from OPT]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/v0.25.3/optimade-version.json
