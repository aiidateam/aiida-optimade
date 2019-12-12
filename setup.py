import json
from pathlib import Path
from setuptools import setup, find_packages

module_dir = Path(__file__).resolve().parent

with open(module_dir.joinpath("setup.json")) as fp:
    SETUP_JSON = json.load(fp)

testing_deps = ["pytest~=3.6", "pytest-cov", "codecov"]
dev_deps = ["pylint", "black", "pre-commit"] + testing_deps

setup(
    long_description=open(module_dir.joinpath("README.md")).read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "aiida-core~=1.0.1",
        "fastapi~=0.44",
        "lark-parser~=0.7.8",
        "optimade~=0.2",
        "pydantic<1.0.0",
        "uvicorn",
    ],
    extras_require={"dev": dev_deps, "testing": testing_deps},
    **SETUP_JSON
)
