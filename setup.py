# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages

module_dir = os.path.dirname(os.path.abspath(__file__))

testing_deps = ["pytest>=3.6", "pytest-cov", "codecov"]
dev_deps = ["pylint", "black", "pre-commit"] + testing_deps

setup(
    name="aiida-optimade",
    version="0.2.0",
    url="https://github.com/aiidateam/aiida-optimade",
    license="MIT License",
    author="The AiiDA team",
    author_email="developers@aiida.net",
    description="Expose an AiiDA database according to the OPTiMaDe specification.",
    long_description=open(os.path.join(module_dir, "README.md")).read(),
    long_description_content_type="text/markdown",
    keywords="optimade aiida materials",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: AiiDA",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Server",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aiida-core>=1.0.0",
        "fastapi==0.44.0",
        "lark-parser>=0.7.7",
        "optimade>=0.2.0",
        "pydantic<1.0.0",
        "uvicorn",
    ],
    extras_require={"dev": dev_deps, "testing": testing_deps},
)
