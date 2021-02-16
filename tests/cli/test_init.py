"""Test CLI `aiida-optimade init` command"""
# pylint: disable=import-error,too-many-locals
import os
import re

import pytest


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is not None,
    reason="Test is not for MongoDB",
)
def test_init_structuredata(run_cli_command, aiida_profile, top_dir, caplog):
    """Test `aiida-optimade -p profile_name init` works for StructureData Nodes.

    Also, check the `-f/--force` option.
    """
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_init
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database
    aiida_profile.reset_db()

    archive = top_dir.joinpath("tests/cli/static/structure_data_nodes.aiida")
    import_data(archive)

    n_structure_data = orm.QueryBuilder().append(orm.StructureData).count()

    result = run_cli_command(cmd_init.init)
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_structure_data} StructureData and CifData Nodes have been initialized."
        in result.stdout
    ), result.stdout

    extras_key = AiidaEntityTranslator.EXTRAS_KEY
    n_updated_structure_data = (
        orm.QueryBuilder()
        .append(orm.StructureData, filters={"extras": {"has_key": extras_key}})
        .count()
    )
    assert n_structure_data == n_updated_structure_data

    # Try again, now all Nodes should have been updated
    result = run_cli_command(cmd_init.init)
    assert "No new StructureData and CifData Nodes found to initialize" in result.stdout

    # Test '-f/--force' option
    options = ["--force"]
    result = run_cli_command(cmd_init.init, options)
    assert (
        f"About to remove OPTIMADE-specific extras for {n_structure_data} Nodes."
        in result.stdout
    ), result.stdout
    assert (
        f"Done removing extra {extras_key!r} in {n_structure_data} Nodes."
        in result.stdout
    ), result.stdout
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_structure_data} StructureData and CifData Nodes have been initialized."
        in result.stdout
    ), result.stdout

    n_updated_structure_data = (
        orm.QueryBuilder()
        .append(orm.StructureData, filters={"extras": {"has_key": extras_key}})
        .count()
    )
    assert n_structure_data == n_updated_structure_data

    # Ensure the database was reported to be updated.
    assert (
        re.match(r".*Updating Node [0-9]+ in AiiDA DB!.*", caplog.text, flags=re.DOTALL)
        is not None
    ), caplog.text

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structures.aiida")
    import_data(original_data)


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is not None,
    reason="Test is not for MongoDB",
)
def test_init_cifdata(run_cli_command, aiida_profile, top_dir, caplog):
    """Test `aiida-optimade -p profile_name init` works for CifData Nodes."""
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_init
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database
    aiida_profile.reset_db()

    archive = top_dir.joinpath("tests/cli/static/cif_data_nodes.aiida")
    import_data(archive)

    n_cif_data = orm.QueryBuilder().append(orm.CifData).count()

    result = run_cli_command(cmd_init.init)
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_cif_data} StructureData and CifData Nodes have been initialized."
        in result.stdout
    ), result.stdout

    extras_key = AiidaEntityTranslator.EXTRAS_KEY
    n_updated_cif_data = (
        orm.QueryBuilder()
        .append(orm.CifData, filters={"extras": {"has_key": extras_key}})
        .count()
    )
    assert n_cif_data == n_updated_cif_data

    # Try again, now all Nodes should have been updated
    result = run_cli_command(cmd_init.init)
    assert "No new StructureData and CifData Nodes found to initialize" in result.stdout

    # Ensure the database was reported to be updated.
    assert (
        re.match(r".*Updating Node [0-9]+ in AiiDA DB!.*", caplog.text, flags=re.DOTALL)
        is not None
    ), caplog.text

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structures.aiida")
    import_data(original_data)


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is None, reason="Test is only for MongoDB"
)
def test_init_structuredata_mongo(run_cli_command, aiida_profile, top_dir, caplog):
    """Test `aiida-optimade -p profile_name init --mongo` works for StructureData Nodes.

    Also, check the `-f/--force` option.
    """
    import bson.json_util
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_init
    from aiida_optimade.routers.structures import STRUCTURES_MONGO
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear databases
    aiida_profile.reset_db()
    STRUCTURES_MONGO.collection.drop()

    archive = top_dir.joinpath("tests/cli/static/structure_data_nodes.aiida")
    import_data(archive)

    n_structure_data = orm.QueryBuilder().append(orm.StructureData).count()

    options = ["--mongo"]
    result = run_cli_command(cmd_init.init, options)
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_structure_data} StructureData and CifData Nodes have been initialized."
        in result.stdout
    ), result.stdout

    extras_key = AiidaEntityTranslator.EXTRAS_KEY
    n_updated_structure_data = (
        orm.QueryBuilder()
        .append(orm.StructureData, filters={"extras": {"has_key": extras_key}})
        .count()
    )
    assert n_updated_structure_data == 0
    assert n_structure_data == len(STRUCTURES_MONGO)

    # Try again, now all Nodes should have been updated
    result = run_cli_command(cmd_init.init, options)
    assert (
        "No new StructureData and CifData Nodes found to initialize" in result.stdout
    ), result.stdout

    # Test '-f/--force' option
    options.append("--force")
    result = run_cli_command(cmd_init.init, options)
    assert (
        f"About to drop structures collection {STRUCTURES_MONGO.collection.full_name!r} in MongoDB."
        in result.stdout
    ), result.stdout
    assert (
        f"Done dropping {STRUCTURES_MONGO.collection.full_name!r} collection."
        in result.stdout
    ), result.stdout
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_structure_data} StructureData and CifData Nodes have been initialized."
        in result.stdout
    ), result.stdout

    n_updated_structure_data = (
        orm.QueryBuilder()
        .append(orm.StructureData, filters={"extras": {"has_key": extras_key}})
        .count()
    )
    assert n_updated_structure_data == 0
    assert n_structure_data == len(STRUCTURES_MONGO)

    # Ensure the database was reported to be updated.
    assert (
        re.match(r".*Upserting Node [0-9]+ in MongoDB!.*", caplog.text, flags=re.DOTALL)
        is not None
    ), caplog.text

    # Repopulate databases with the "proper" test data
    aiida_profile.reset_db()
    import_data(top_dir.joinpath("tests/static/test_structures.aiida"))
    STRUCTURES_MONGO.collection.drop()
    with open(top_dir.joinpath("tests/static/test_structures_mongo.json")) as handle:
        data = bson.json_util.loads(handle.read())
    STRUCTURES_MONGO.collection.insert_many(data)


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is None, reason="Test is only for MongoDB"
)
def test_init_cifdata_mongo(run_cli_command, aiida_profile, top_dir, caplog):
    """Test `aiida-optimade -p profile_name init` works for CifData Nodes."""
    import bson.json_util
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_init
    from aiida_optimade.routers.structures import STRUCTURES_MONGO
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear databases
    aiida_profile.reset_db()
    STRUCTURES_MONGO.collection.drop()

    archive = top_dir.joinpath("tests/cli/static/cif_data_nodes.aiida")
    import_data(archive)

    n_cif_data = orm.QueryBuilder().append(orm.CifData).count()

    options = ["--mongo"]
    result = run_cli_command(cmd_init.init, options)
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_cif_data} StructureData and CifData Nodes have been initialized."
        in result.stdout
    ), result.stdout

    extras_key = AiidaEntityTranslator.EXTRAS_KEY
    n_updated_cif_data = (
        orm.QueryBuilder()
        .append(orm.CifData, filters={"extras": {"has_key": extras_key}})
        .count()
    )
    assert n_updated_cif_data == 0
    assert n_cif_data == len(STRUCTURES_MONGO)

    # Try again, now all Nodes should have been updated
    result = run_cli_command(cmd_init.init, options)
    assert (
        "No new StructureData and CifData Nodes found to initialize" in result.stdout
    ), result.stdout

    # Ensure the database was reported to be updated.
    assert (
        re.match(r".*Upserting Node [0-9]+ in MongoDB!.*", caplog.text, flags=re.DOTALL)
        is not None
    ), caplog.text

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    import_data(top_dir.joinpath("tests/static/test_structures.aiida"))
    STRUCTURES_MONGO.collection.drop()
    with open(top_dir.joinpath("tests/static/test_structures_mongo.json")) as handle:
        data = bson.json_util.loads(handle.read())
    STRUCTURES_MONGO.collection.insert_many(data)
