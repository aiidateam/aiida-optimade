import re

from invoke import task

from aiida_optimade import __version__


@task
def setver(_, patch=False, new_ver=""):
    """Update the package version throughout the package"""

    if (not patch and not new_ver) or (patch and new_ver):
        raise Exception(
            "Either use --patch or specify e.g. "
            "--new-ver='Major.Minor.Patch(a|b|rc)?[0-9]+'"
        )
    if patch:
        ver = [int(x) for x in __version__.split(".")]
        ver[2] += 1
        new_ver = ".".join(map(str, ver))
    with open("aiida_optimade/__init__.py", "r") as handle:
        lines = [
            re.sub("__version__ = .+", '__version__ = "{}"'.format(new_ver), l.rstrip())
            for l in handle
        ]
    with open("aiida_optimade/__init__.py", "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")

    with open("setup.json", "r") as handle:
        lines = [
            re.sub(
                '"version": ([^,]+),', '"version": "{}",'.format(new_ver), l.rstrip()
            )
            for l in handle
        ]
    with open("setup.json", "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")

    with open("aiida_optimade/config.json", "r") as handle:
        lines = [
            re.sub(
                '"version": ([^,]+),', '"version": "{}",'.format(new_ver), l.rstrip()
            )
            for l in handle
        ]
    with open("aiida_optimade/config.json", "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")

    print("Bumped version to {}".format(new_ver))


@task
def optimade_req(_, ver=""):
    """Update the optimade-python-tools minimum version requirement"""

    if not ver:
        raise Exception("Please specify --ver='Major.Minor.Patch'")

    with open("setup.py", "r") as handle:
        lines = [
            re.sub("optimade~=([^,]+)", f'optimade~={ver}"', l.rstrip()) for l in handle
        ]
    with open("setup.py", "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")

    with open("README.md", "r") as handle:
        lines = [
            re.sub(
                "https://raw.githubusercontent.com/Materials-Consortia/"
                "optimade-python-tools/v([^,]+)/.ci/",
                "https://raw.githubusercontent.com/Materials-Consortia/"
                f"optimade-python-tools/v{ver}/.ci/",
                l.rstrip("\n"),
            )
            for l in handle
        ]
    with open("README.md", "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")

    with open("Dockerfile", "r") as handle:
        lines = [
            re.sub(
                "OPTIMADE_TOOLS_VERSION=.*", f"OPTIMADE_TOOLS_VERSION={ver}", l.rstrip()
            )
            for l in handle
        ]

    with open("Dockerfile", "w") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")

    for file_format in ("j2", "yml"):
        with open(f"profiles/docker-compose.{file_format}", "r") as handle:
            lines = [
                re.sub(
                    "OPTIMADE_TOOLS_VERSION: .*",
                    f"OPTIMADE_TOOLS_VERSION: {ver}",
                    l.rstrip(),
                )
                for l in handle
            ]

        with open(f"profiles/docker-compose.{file_format}", "w") as handle:
            handle.write("\n".join(lines))
            handle.write("\n")

    print("Bumped OPTiMaDe Python Tools version requirement to {}".format(ver))
