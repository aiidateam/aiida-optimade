import re

from invoke import task

from aiida_optimade import __version__


@task
def setver(_, patch=False, new_ver=""):
    if (not patch and not new_ver) or (patch and new_ver):
        raise Exception(
            "Either use --patch or specify e.g. --new-ver='Major.Minor.Patch(a|b|rc)?[0-9]+'"
        )
    if patch:
        v = [int(x) for x in __version__.split(".")]
        v[2] += 1
        new_ver = ".".join(map(str, v))
    with open("aiida_optimade/__init__.py", "r") as f:
        lines = [
            re.sub("__version__ = .+", '__version__ = "{}"'.format(new_ver), l.rstrip())
            for l in f
        ]
    with open("aiida_optimade/__init__.py", "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    with open("setup.json", "r") as f:
        lines = [
            re.sub(
                '"version": ([^,]+),', '"version": "{}",'.format(new_ver), l.rstrip()
            )
            for l in f
        ]
    with open("setup.json", "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    with open("aiida_optimade/config.json", "r") as f:
        lines = [
            re.sub(
                '"version": ([^,]+),', '"version": "{}",'.format(new_ver), l.rstrip()
            )
            for l in f
        ]
    with open("aiida_optimade/config.json", "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    print("Bumped version to {}".format(new_ver))


@task
def set_optimade_ver(_, ver=""):
    if not ver:
        raise Exception("Please specify --ver='Major.Minor.Patch'")
    with open("aiida_optimade/config.json", "r") as f:
        lines = [
            re.sub(
                '"api_version": ([^,]+),',
                '"api_version": "{}",'.format(ver),
                l.rstrip(),
            )
            for l in f
        ]
    with open("aiida_optimade/config.json", "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    with open(".ci/optimade-version.json", "r") as f:
        lines = [
            re.sub('"message": .+', '"message": "v{}",'.format(ver), l.rstrip())
            for l in f
        ]
    with open(".ci/optimade-version.json", "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

    print("Bumped OPTiMaDe version to {}".format(ver))
