# pylint: disable=unused-argument
import os
from pathlib import Path


def pytest_configure(config):
    """Method that runs before pytest collects tests so no modules are imported"""
    set_config_file()
    load_aiida_profile()


def set_config_file():
    """Set config file environment variable pointing to `/tests/test_config.json`"""
    cwd = Path(__file__).parent.resolve()
    os.environ["OPTIMADE_CONFIG_FILE"] = str(cwd.joinpath("test_config.json"))


def load_aiida_profile():
    """Load AiiDA profile"""
    if os.getenv("AIIDA_PROFILE", None) is None:
        os.environ["AIIDA_PROFILE"] = "optimade_sqla"
