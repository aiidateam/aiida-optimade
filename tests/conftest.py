# pylint: disable=unused-argument,redefined-outer-name,import-error
import os
from pathlib import Path

import pytest

pytest_plugins = ["aiida.manage.tests.pytest_fixtures"]


@pytest.fixture(scope="session")
def top_dir() -> Path:
    """Return Path instance for the repository's top (root) directory"""
    return Path(__file__).parent.parent.resolve()


@pytest.fixture(scope="session", autouse=True)
def setup_config(top_dir) -> None:
    """Method that runs before pytest collects tests so no modules are imported"""
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
def aiida_profile_populated(top_dir, setup_config, aiida_profile):
    """Load test data for AiiDA test profile"""
    from aiida.tools.archive.imports import import_archive

    org_env_var = os.getenv("AIIDA_PROFILE")
    test_env_var = os.getenv("PYTEST_OPTIMADE_CONFIG_FILE")

    try:
        aiida_profile.clear_profile()

        # If test locally `AIIDA_TEST_PROFILE` may not set and `test_profile` will be used
        # assert profile.name in ["test_profile", "test_psql_dos"]
        os.environ["AIIDA_PROFILE"] = aiida_profile.name

        # Use AiiDA DB
        import_archive(top_dir.joinpath("tests/static/test_structures.aiida"))

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
                top_dir.joinpath("tests/static/test_structures_mongo.json")
            ) as handle:
                data = bson.json_util.loads(handle.read())
            STRUCTURES_MONGO.collection.insert_many(data)

        yield aiida_profile
    finally:
        if org_env_var is not None:
            os.environ["AIIDA_PROFILE"] = org_env_var
        elif "AIIDA_PROFILE" in os.environ:
            del os.environ["AIIDA_PROFILE"]


@pytest.fixture
def get_valid_id() -> str:
    """Get a currently valid ID/PK from a StructureData Node"""
    from optimade.server.config import CONFIG, SupportedBackend

    if CONFIG.database_backend == SupportedBackend.MONGODB:
        from aiida_optimade.routers.structures import STRUCTURES_MONGO

        return STRUCTURES_MONGO.collection.find_one({}, projection=["id"])["id"]

    from aiida.orm import QueryBuilder, StructureData

    return QueryBuilder().append(StructureData, project="id").first()[0]
