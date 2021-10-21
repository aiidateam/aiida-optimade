import re
from typing import Tuple

from invoke import task


def update_file(filename: str, sub_line: Tuple[str, str], strip: str = None):
    """Utility function for tasks to read, update, and write files"""
    with open(filename, "r") as handle:
        lines = [
            re.sub(sub_line[0], sub_line[1], line.rstrip(strip)) for line in handle
        ]

    with open(filename, "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


@task
def setver(_, patch=False, version=""):
    """Update the package version throughout the package"""
    if (not patch and not version) or (patch and version):
        raise RuntimeError(
            "Either use --patch or specify e.g. "
            '--version="Major.Minor.Patch(a|b|rc)?[0-9]+"'
        )
    if patch:
        from aiida_optimade import __version__

        ver = [int(x) for x in __version__.split(".")]
        ver[2] += 1
        version = ".".join(map(str, ver))
    elif version:
        if version.startswith("v"):
            version = version[1:]
        if re.match(r"[0-9]+(\.[0-9]+){2}", version) is None:
            raise ValueError("version MUST be specified as 'Major.Minor.Patch'")

    update_file(
        "aiida_optimade/__init__.py", ("__version__ = .+", f'__version__ = "{version}"')
    )
    update_file("setup.json", ('"version": ([^,]+),', f'"version": "{version}",'))
    update_file(
        "aiida_optimade/config.json",
        ('"version": ([^,]+),', f'"version": "{version}",'),
    )
    update_file(
        "tests/static/test_config.json",
        ('"version": ([^,]+),', f'"version": "{version}",'),
    )
    update_file(
        "tests/static/test_mongo_config.json",
        ('"version": ([^,]+),', f'"version": "{version}",'),
    )
    update_file(
        ".github/mongo/ci_config.json",
        ('"version": ([^,]+),', f'"version": "{version}",'),
    )

    print(f"Bumped version to {version}")


@task
def optimade_req(_, ver=""):
    """Update the optimade-python-tools minimum version requirement"""
    import requests

    if not ver:
        raise RuntimeError("Please specify --ver='Major.Minor.Patch'")
    if ver.startswith("v"):
        ver = ver[1:]
    if not re.match(r"[0-9]+(\.[0-9]+){2}", ver):
        raise ValueError("ver MUST be specified as 'Major.Minor.Patch'")

    optimade_init = requests.get(
        "https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools"
        f"/v{ver}/optimade/__init__.py"
    )
    if optimade_init.status_code != 200:
        raise RuntimeError(f"{ver} does not seem to be published on GitHub")

    semver_regex = (
        r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\."
        r"(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
    )

    api_version_tuple = re.findall(
        semver_regex, re.findall('__api_version__ = ".*"', optimade_init.text)[0]
    )[0]
    api_version = ".".join(api_version_tuple[:3])
    if api_version_tuple[3]:
        api_version += f"-{api_version[3]}"
    if api_version_tuple[4]:
        api_version += f"+{api_version[4]}"

    update_file(
        "requirements.txt", (r"optimade\[mongo\]~=.+", f"optimade[mongo]~={ver}")
    )
    update_file(
        "README.md",
        (
            "https://raw.githubusercontent.com/Materials-Consortia/"
            "optimade-python-tools/v([^,]+)/optimade-",
            "https://raw.githubusercontent.com/Materials-Consortia/"
            f"optimade-python-tools/v{ver}/optimade-",
        ),
        strip="\n",
    )
    update_file(
        "Dockerfile", ("OPTIMADE_TOOLS_VERSION=.*", f"OPTIMADE_TOOLS_VERSION={ver}")
    )
    for file_format in ("j2", "yml"):
        for docker_compose_file in ("", "-mongo"):
            update_file(
                f"profiles/docker-compose{docker_compose_file}.{file_format}",
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
        update_file("README.md", (f"/v{regex}/info", f"/v{version}/info"), strip="\n")

    print(f"Bumped OPTIMADE Python Tools version requirement to {ver}")


@task
def aiida_req(_, ver=""):
    """Update the aiida-core minimum version requirement"""
    if not ver:
        raise RuntimeError("Please specify --ver='Major.Minor.Patch'")
    if ver.startswith("v"):
        ver = ver[1:]

    update_file("requirements.txt", ("aiida-core~=.+", f"aiida-core~={ver}"))
    update_file(".ci/aiida-version.json", ('"message": .+', f'"message": "v{ver}",'))
    update_file("Dockerfile", ("AIIDA_VERSION=.*", f"AIIDA_VERSION={ver}"))
    for file_format in ("j2", "yml"):
        for docker_compose_file in ("", "-mongo"):
            update_file(
                f"profiles/docker-compose{docker_compose_file}.{file_format}",
                ("AIIDA_VERSION: .*", f"AIIDA_VERSION: {ver}"),
            )

    print(f"Bumped AiiDA Core version requirement to {ver}")
