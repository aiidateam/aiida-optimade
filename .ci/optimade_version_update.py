import json
import sys
from pathlib import Path

SHIELDS_JSON = Path(__file__).resolve().parent.joinpath("optimade-version.json")
CONFIG_JSON = (
    Path(__file__).resolve().parent.parent.joinpath("aiida_optimade/config.json")
)

with open(SHIELDS_JSON, "r") as fp:
    SHIELD = json.load(fp)

with open(CONFIG_JSON, "r") as fp:
    CONFIG = json.load(fp)

SHIELD_VERSION = SHIELD["message"]
CURRENT_VERSION = f"v{CONFIG['api_version']}"

if SHIELD_VERSION == CURRENT_VERSION:
    # The shield has the newest implemented version
    print(
        f"""They are the same: {CURRENT_VERSION}
Shield file:
{json.dumps(SHIELD, indent=2)}"""
    )
    sys.exit(0)

print(
    f"""The shield version is outdated.
Shield version: {SHIELD_VERSION}
Current version: {CURRENT_VERSION}
"""
)

SHIELD["message"] = CURRENT_VERSION
with open(SHIELDS_JSON, "w") as fp:
    json.dump(SHIELD, fp, indent=2)
    fp.write("\n")

# Check file was saved correctly
with open(SHIELDS_JSON, "r") as fp:
    UPDATE_SHIELD = json.load(fp)

if UPDATE_SHIELD["message"] == CURRENT_VERSION:
    print(f"Successfully updated the shield version to {UPDATE_SHIELD['message']}")
    sys.exit(0)
else:
    print(
        f"""Something went wrong !
Shield file:
{json.dumps(UPDATE_SHIELD, indent=2)}"""
    )
    sys.exit(1)
