# pylint: disable=line-too-long
import os
import json
import sys
from pathlib import Path

SETUP_JSON = Path(__file__).resolve().parent.parent.joinpath("setup.json")

with open(SETUP_JSON, "r") as fp:
    SETUP = json.load(fp)

PACKAGE_VERSION = "v" + SETUP["version"]

TAG_VERSION = os.getenv("TAG_VERSION")
TAG_VERSION = TAG_VERSION[len("refs/tags/") :]  # noqa: E203

if TAG_VERSION == PACKAGE_VERSION:
    print(f"The versions match: tag:'{TAG_VERSION}' == package:'{PACKAGE_VERSION}'")
    sys.exit(0)

print(
    f"""The current package version '{PACKAGE_VERSION}' does not equal the tag version '{TAG_VERSION}'.
Update setup.json with new version.
Please remove the tag from both GitHub and your local repository!"""
)
sys.exit(1)
