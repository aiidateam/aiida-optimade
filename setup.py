import json
from pathlib import Path
from setuptools import setup, find_packages

MODULE_DIR = Path(__file__).resolve().parent

with open(MODULE_DIR.joinpath("setup.json")) as handle:
    SETUP_JSON = json.load(handle)

with open(MODULE_DIR.joinpath("requirements.txt")) as handle:
    REQUIREMENTS = [f"{_.strip()}" for _ in handle.readlines()]

with open(MODULE_DIR.joinpath("requirements_testing.txt")) as handle:
    TESTING = [f"{_.strip()}" for _ in handle.readlines()]

with open(MODULE_DIR.joinpath("requirements_dev.txt")) as handle:
    DEV = [f"{_.strip()}" for _ in handle.readlines()] + TESTING

setup(
    long_description=open(MODULE_DIR.joinpath("README.md")).read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "profiles"]),
    python_requires=">=3.6",
    install_requires=REQUIREMENTS,
    extras_require={"dev": DEV, "testing": TESTING},
    entry_points={
        "console_scripts": [
            "aiida-optimade = aiida_optimade.cli.cmd_aiida_optimade:cli",
        ],
    },
    **SETUP_JSON,
)
