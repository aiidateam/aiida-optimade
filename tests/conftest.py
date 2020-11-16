# pylint: disable=unused-argument,redefined-outer-name
import os
from pathlib import Path

import pytest

from aiida.manage.tests import TestManager


@pytest.fixture(scope="session")
def top_dir() -> Path:
    """Return Path instance for the repository's top (root) directory"""
    return Path(__file__).parent.parent.resolve()


@pytest.fixture(scope="session", autouse=True)
def setup_config(top_dir):
    """Method that runs before pytest collects tests so no modules are imported"""
    filename = top_dir.joinpath("tests/static/test_config.json")

    original_env_var = os.getenv("OPTIMADE_CONFIG_FILE")
    try:
        os.environ["OPTIMADE_CONFIG_FILE"] = str(filename)
        yield
    finally:
        if original_env_var is not None:
            os.environ["OPTIMADE_CONFIG_FILE"] = original_env_var
        elif "OPTIMADE_CONFIG_FILE" in os.environ:
            del os.environ["OPTIMADE_CONFIG_FILE"]


@pytest.fixture(scope="session", autouse=True)
def aiida_profile(top_dir) -> TestManager:
    """Load test data for AiiDA test profile

    It is necessary to remove `AIIDA_PROFILE`, since it clashes with the test profile
    """
    from aiida import load_profile
    from aiida.manage.tests import (
        get_test_backend_name,
        get_test_profile_name,
        test_manager,
    )
    from aiida.tools.importexport import import_data

    org_env_var = os.getenv("AIIDA_PROFILE")

    try:
        # Setup profile
        with test_manager(
            backend=get_test_backend_name(), profile_name=get_test_profile_name()
        ) as manager:
            manager.reset_db()

            profile = load_profile().name
            assert profile in ["test_profile", "test_django", "test_sqlalchemy"]
            os.environ["AIIDA_PROFILE"] = profile

            filename = top_dir.joinpath("tests/static/test_structuredata.aiida")
            import_data(filename)

            yield manager
    finally:
        if org_env_var is not None:
            os.environ["AIIDA_PROFILE"] = org_env_var
        elif "AIIDA_PROFILE" in os.environ:
            del os.environ["AIIDA_PROFILE"]


@pytest.fixture
def get_valid_id() -> str:
    """Get a currently valid ID/PK from a StructureData Node"""
    from aiida.orm import QueryBuilder, StructureData

    builder = QueryBuilder().append(StructureData, project="id")
    return builder.first()[0]
