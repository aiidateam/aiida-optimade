import re
from typing import Tuple
import requests

from invoke import task

from aiida_optimade import __version__


def update_file(filename: str, sub_line: Tuple[str, str], strip: str = None):
    """Utility function for tasks to read, update, and write files"""
    with open(filename, "r") as handle:
        lines = [re.sub(sub_line[0], sub_line[1], l.rstrip(strip)) for l in handle]

    with open(filename, "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


@task
def setver(_, patch=False, new_ver=""):
    """Update the package version throughout the package"""

    if (not patch and not new_ver) or (patch and new_ver):
        raise Exception(
            "Either use --patch or specify e.g. "
            '--new-ver="Major.Minor.Patch(a|b|rc)?[0-9]+"'
        )
    if patch:
        ver = [int(x) for x in __version__.split(".")]
        ver[2] += 1
        new_ver = ".".join(map(str, ver))

    update_file(
        "aiida_optimade/__init__.py", ("__version__ = .+", f'__version__ = "{new_ver}"')
    )
    update_file("setup.json", ('"version": ([^,]+),', f'"version": "{new_ver}",'))
    update_file(
        "aiida_optimade/config.json",
        ('"version": ([^,]+),', f'"version": "{new_ver}",'),
    )
    update_file(
        "tests/test_config.json", ('"version": ([^,]+),', f'"version": "{new_ver}",'),
    )

    print("Bumped version to {}".format(new_ver))


@task
def optimade_req(_, ver=""):
    """Update the optimade-python-tools minimum version requirement"""

    if not ver:
        raise Exception("Please specify --ver='Major.Minor.Patch'")
    if not re.match("[0-9]+.[0-9]+.[0-9]+", ver):
        raise Exception("ver MUST be specified as 'Major.Minor.Patch'")

    optimade_init = requests.get(
        "https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools"
        f"/v{ver}/optimade/__init__.py"
    )
    if optimade_init.status_code != 200:
        raise Exception(f"{ver} does not seem to be published on GitHub")

    semver_regex = (
        r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\."
        r"(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
    )

    api_version_tuple = re.findall(
        semver_regex, re.findall('__api_version__ = ".*"', optimade_init.text)[0],
    )[0]
    api_version = ".".join(api_version_tuple[:3])
    if api_version_tuple[3]:
        api_version += f"-{api_version[3]}"
    if api_version_tuple[4]:
        api_version += f"+{api_version[4]}"

    update_file("setup.py", (r"optimade\[mongo\]~=([^,]+)", f'optimade[mongo]~={ver}"'))
    update_file(
        "README.md",
        (
            "https://raw.githubusercontent.com/Materials-Consortia/"
            "optimade-python-tools/v([^,]+)/.ci/",
            "https://raw.githubusercontent.com/Materials-Consortia/"
            f"optimade-python-tools/v{ver}/.ci/",
        ),
        strip="\n",
    )
    update_file(
        "Dockerfile", ("OPTIMADE_TOOLS_VERSION=.*", f"OPTIMADE_TOOLS_VERSION={ver}")
    )
    for file_format in ("j2", "yml"):
        update_file(
            f"profiles/docker-compose.{file_format}",
            ("OPTIMADE_TOOLS_VERSION: .*", f"OPTIMADE_TOOLS_VERSION: {ver}"),
        )
    for regex, version in (
        (r"[0-9]+", api_version.split("-")[0].split("+")[0].split(".")[0]),
        (
            r"[0-9]+\.[0-9]+",
            ".".join(api_version.split("-")[0].split("+")[0].split(".")[:2]),
        ),
        (r"[0-9]+\.[0-9]+\.[0-9]+", api_version.split("-")[0].split("+")[0]),
    ):
        update_file(".github/workflows/ci.yml", (f"/v{regex}", f"/v{version}"))
        update_file("README.md", (f"/v{regex}/info", f"/v{version}/info"), strip="\n")

    print("Bumped OPTIMADE Python Tools version requirement to {}".format(ver))


@task
def aiida_req(_, ver=""):
    """Update the aiida-core minimum version requirement"""

    if not ver:
        raise Exception("Please specify --ver='Major.Minor.Patch'")

    update_file("setup.py", ("aiida-core~=([^,]+)", f'aiida-core~={ver}"'))
    update_file(".ci/aiida-version.json", ('"message": .+', f'"message": "v{ver}",'))
    update_file("Dockerfile", ("AIIDA_VERSION=.*", f"AIIDA_VERSION={ver}"))
    for file_format in ("j2", "yml"):
        update_file(
            f"profiles/docker-compose.{file_format}",
            ("AIIDA_VERSION: .*", f"AIIDA_VERSION: {ver}"),
        )

    print("Bumped AiiDA Core version requirement to {}".format(ver))
