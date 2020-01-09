import json
from pathlib import Path
from setuptools import setup, find_packages

MODULE_DIR = Path(__file__).resolve().parent

with open(MODULE_DIR.joinpath("setup.json")) as handle:
    SETUP_JSON = json.load(handle)

TESTING = ["pytest~=3.6", "pytest-cov", "codecov"]
DEV = ["pylint", "black", "pre-commit", "invoke"] + TESTING

setup(
    long_description=open(MODULE_DIR.joinpath("README.md")).read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "aiida-core~=1.0.1",
        "fastapi~=0.44",
        "lark-parser~=0.7.8",
        "optimade~=0.2",
        "pydantic~=1.0, <2.0.0",
        "uvicorn",
    ],
    extras_require={"dev": DEV, "testing": TESTING},
    **SETUP_JSON
)
