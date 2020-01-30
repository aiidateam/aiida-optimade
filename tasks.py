import re
from typing import Tuple

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

    print("Bumped version to {}".format(new_ver))


@task
def optimade_req(_, ver=""):
    """Update the optimade-python-tools minimum version requirement"""

    if not ver:
        raise Exception("Please specify --ver='Major.Minor.Patch'")

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

    print("Bumped OPTiMaDe Python Tools version requirement to {}".format(ver))
