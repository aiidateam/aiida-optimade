# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="aiida-optimade",
    version="0.10.0",
    packages=find_packages(),
    license="MIT Licence",
    author="The AiiDA team",
    install_requires=[
        #"optimade==0.2.0",
        "lark-parser==0.5.6",
        "fastapi[all]==0.28.0",
        "aiida-core>=1.0.0",
    ],
)
