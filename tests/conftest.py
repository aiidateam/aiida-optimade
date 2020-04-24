# pylint: disable=unused-import,unused-argument
import os
from pathlib import Path

import pytest


def pytest_configure(config):
    """Method that runs before pytest collects tests so no modules are imported"""
    config_file = Path(__file__).parent.parent.joinpath("aiida_optimade/config.json")
    os.environ["OPTIMADE_CONFIG_FILE"] = str(config_file)
