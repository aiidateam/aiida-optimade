# pylint: disable=unused-argument,redefined-outer-name,import-error
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Generator

    from aiida.manage.tests import TestManager


@pytest.fixture(scope="session")
def top_dir() -> "Path":
    """Return Path instance for the repository's top (root) directory"""
    from pathlib import Path

    return Path(__file__).parent.parent.resolve()


@pytest.fixture(scope="session", autouse=True)
def setup_config(top_dir: "Path") -> "Generator[None, None, None]":
    """Method that runs before pytest collects tests so no modules are imported"""
    import os

    filename = top_dir / "tests/static/test_config.json"

    original_env_var = os.getenv("OPTIMADE_CONFIG_FILE")

    try:
        os.environ["OPTIMADE_CONFIG_FILE"] = os.getenv(
            "PYTEST_OPTIMADE_CONFIG_FILE"
        ) or str(filename)
        yield
    finally:
        if original_env_var is not None:
            os.environ["OPTIMADE_CONFIG_FILE"] = original_env_var
        elif "OPTIMADE_CONFIG_FILE" in os.environ:
            del os.environ["OPTIMADE_CONFIG_FILE"]


@pytest.fixture(scope="session", autouse=True)
@pytest.mark.usefixtures("setup_config")
def aiida_profile(top_dir: "Path") -> "Generator[TestManager, None, None]":
    """Load test data for AiiDA test profile

    It is necessary to remove `AIIDA_PROFILE`, since it clashes with the test profile
    """
    import os

    from aiida.manage.configuration import load_profile
    from aiida.manage.tests import (
        get_test_backend_name,
        get_test_profile_name,
        test_manager,
    )
    from aiida.tools.archive.imports import import_archive

    org_env_var = os.getenv("AIIDA_PROFILE")
    test_env_var = os.getenv("PYTEST_OPTIMADE_CONFIG_FILE")

    try:
        # Setup profile
        with test_manager(
            backend=get_test_backend_name(), profile_name=get_test_profile_name()
        ) as manager:
            manager.reset_db()

            profile = load_profile()
            # If test locally `AIIDA_TEST_PROFILE` may not set and `test_profile` will
            # be used
            assert profile.name in ["test_profile", "test_psql_dos"]
            os.environ["AIIDA_PROFILE"] = profile.name

            # Use AiiDA DB
            import_archive(top_dir / "tests" / "static" / "test_structures.aiida")

            if test_env_var:
                # Use MongoDB
                assert os.getenv("OPTIMADE_CONFIG_FILE", "") == test_env_var, (
                    "Config file env var not set prior to updating the MongoDB! Found "
                    "it to be a MongoDB backend, since PYTEST_OPTIMADE_CONFIG_FILE is "
                    f"set to {test_env_var}"
                )
                import bson.json_util

                from aiida_optimade.routers.structures import STRUCTURES_MONGO

                STRUCTURES_MONGO.collection.drop()
                with open(
                    top_dir / "tests" / "static" / "test_structures_mongo.json",
                    encoding="utf8",
                ) as handle:
                    data = bson.json_util.loads(handle.read())
                STRUCTURES_MONGO.collection.insert_many(data)

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
    from optimade.server.config import CONFIG, SupportedBackend

    if CONFIG.database_backend == SupportedBackend.MONGODB:
        from aiida_optimade.routers.structures import STRUCTURES_MONGO

        node = STRUCTURES_MONGO.collection.find_one({}, projection=["id"])
        if node is None:
            raise RuntimeError("No structures found in test DB !!!")
        return node["id"]

    return QueryBuilder().append(StructureData, project="id").first(True)
