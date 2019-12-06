import os
import json
from pathlib import Path

SETUP_JSON = Path(__file__).resolve().parent.parent.joinpath("setup.json")

with open(SETUP_JSON, "r") as fp:
    setup = json.load(fp)

package_version = "v" + setup["version"]

tag_version = os.getenv("TAG_VERSION")
tag_version = tag_version[len("refs/tags/") :]

if tag_version == package_version:
    print(f"The versions match: tag:'{tag_version}' == package:'{package_version}'")
    exit(0)

print(
    f"""The current package version '{package_version}' does not equal the tag version '{tag_version}'.
Please remove the tag from both GitHub and your fork!"""
)
exit(1)
