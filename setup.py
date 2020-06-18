import json
from pathlib import Path
from setuptools import setup, find_packages

MODULE_DIR = Path(__file__).resolve().parent

with open(MODULE_DIR.joinpath("setup.json")) as handle:
    SETUP_JSON = json.load(handle)

TESTING = ["pytest~=5.4", "pytest-cov~=2.10", "codecov~=2.1"]
DEV = ["pylint~=2.5", "black~=19.10b0", "pre-commit~=2.5", "invoke~=1.4"] + TESTING

setup(
    long_description=open(MODULE_DIR.joinpath("README.md")).read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "aiida-core~=1.2.1",
        "fastapi~=0.58.0",
        "lark-parser~=0.8.9",
        "optimade[mongo]~=0.9.1",
        "pydantic~=1.5",
        "uvicorn~=0.11.5",
    ],
    extras_require={"dev": DEV, "testing": TESTING},
    **SETUP_JSON
)
