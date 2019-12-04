import json
from pathlib import Path

from aiida_optimade.config import CONFIG

shields_json = Path(__file__).resolve().parent.joinpath("optimade-version.json")

with open(shields_json, "r") as fp:
    shield = json.load(fp)

shield_version = shield["message"]
current_version = CONFIG.version

if shield_version == current_version:
    # The shield has the newest implemented version
    print(
        f"""They are the same: {current_version}
Shield file:
{json.dumps(shield, indent=2)}"""
    )
    exit(0)

print(
    f"""The shield version is outdated.
Shield version: {shield_version}
Current version: {current_version}
"""
)

shield["message"] = current_version
with open(shields_json, "w") as fp:
    json.dump(shield, fp, indent=2)

# Check file was saved correctly
with open(shields_json, "r") as fp:
    update_shield = json.load(fp)

if update_shield["message"] == current_version:
    print(f"Successfully updated the shield version to {update_shield['message']}")
    exit(0)
else:
    print(
        f"""Something went wrong !
Shield file:
{json.dumps(update_shield, indent=2)}"""
    )
    exit(1)
