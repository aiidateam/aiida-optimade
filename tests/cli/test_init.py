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
        f"{n_structure_data} StructureData and CifData Nodes or MongoDB documents have"
        " been initialized." in result.stdout
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
    assert (
        "No new StructureData and CifData Nodes or MongoDB documents found to "
        "initialize" in result.stdout
    )

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
        f"{n_structure_data} StructureData and CifData Nodes or MongoDB documents have"
        " been initialized." in result.stdout
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
        f"{n_cif_data} StructureData and CifData Nodes or MongoDB documents have been "
        "initialized." in result.stdout
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
    assert (
        "No new StructureData and CifData Nodes or MongoDB documents found to "
        "initialize" in result.stdout
    )

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
        f"{n_structure_data} StructureData and CifData Nodes or MongoDB documents have"
        " been initialized." in result.stdout
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
        "No new StructureData and CifData Nodes or MongoDB documents found to "
        "initialize" in result.stdout
    ), result.stdout

    # Test '-f/--force' option
    options.append("--force")
    result = run_cli_command(cmd_init.init, options)
    assert (
        f"About to drop structures collection {STRUCTURES_MONGO.collection.full_name!r}"
        " in MongoDB." in result.stdout
    ), result.stdout
    assert (
        f"Done dropping {STRUCTURES_MONGO.collection.full_name!r} collection."
        in result.stdout
    ), result.stdout
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_structure_data} StructureData and CifData Nodes or MongoDB documents have"
        " been initialized." in result.stdout
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
        f"{n_cif_data} StructureData and CifData Nodes or MongoDB documents have been "
        "initialized." in result.stdout
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
        "No new StructureData and CifData Nodes or MongoDB documents found to "
        "initialize" in result.stdout
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


def test_get_documents(top_dir):
    """Test get_documents()"""
    import bson.json_util
    from aiida_optimade.cli.cmd_init import get_documents, read_chunks

    archive = top_dir.joinpath("tests/static/test_structures_mongo.json").resolve()

    all_loaded_documents = []
    with open(archive) as handle:
        for documents in get_documents(read_chunks(handle, chunk_size=2**24)):
            loaded_documents = bson.json_util.loads(documents)
            assert isinstance(loaded_documents, list)
            all_loaded_documents.extend(loaded_documents)

    with open(archive) as handle:
        documents_pure = bson.json_util.loads(handle.read())

    assert len(all_loaded_documents) == len(documents_pure)
    assert all_loaded_documents == documents_pure


@pytest.mark.parametrize(
    "bad_file", ["", '[{ {"key": "value"}]', '[/{"key": "value"}]']
)
def test_get_documents_bad_file(bad_file):
    """Test get_documents() with syntactically bad files"""
    import tempfile

    def load_documents(handle, all_loaded_documents):
        """Helper function for test"""
        import bson.json_util
        from aiida_optimade.cli.cmd_init import get_documents, read_chunks

        for documents in get_documents(read_chunks(handle, chunk_size=2)):
            loaded_documents = bson.json_util.loads(documents)
            assert isinstance(loaded_documents, list)
            all_loaded_documents.extend(loaded_documents)

    with tempfile.NamedTemporaryFile(mode="w+") as handle:
        handle.write(bad_file)
        handle.seek(0, 0)
        assert handle.tell() == 0

        all_loaded_documents = []
        if "/" in bad_file:
            with pytest.raises(
                SyntaxError, match=r"^Chunk found, but it is not self-consistent.*"
            ):
                load_documents(handle, all_loaded_documents)
        else:
            load_documents(handle, all_loaded_documents)
        assert not all_loaded_documents


def test_filename_aiida(run_cli_command, top_dir):
    """Ensure init excepts when using --filename without --mongo"""
    from aiida_optimade.cli import cmd_init

    real_existing_file = top_dir.joinpath("setup.py")

    options = ["--filename", str(real_existing_file)]
    result = run_cli_command(cmd_init.init, options, raises=True)
    assert "Success:" not in result.stdout, result.stdout
    assert "Critical:" in result.stdout, result.stdout
    assert (
        "An exception happened while trying to initialize" in result.stdout
    ), result.stdout
    assert (
        "NotImplementedError('Passing a filename currently only works for a MongoDB backend'"
        in result.stdout
    ), result.stdout


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is None, reason="Test is only for MongoDB"
)
def test_filename_mongo(run_cli_command, top_dir):
    """Ensure --filename works with --mongo"""
    import bson.json_util

    from aiida_optimade.cli import cmd_init
    from aiida_optimade.routers.structures import STRUCTURES_MONGO

    n_data = len(STRUCTURES_MONGO)

    # Clear database
    STRUCTURES_MONGO.collection.drop()
    assert len(STRUCTURES_MONGO) == 0

    mongo_file = top_dir.joinpath("tests/static/test_structures_mongo.json")

    options = ["--mongo", "--filename", str(mongo_file)]
    result = run_cli_command(cmd_init.init, options)
    assert (
        f"Initializing MongoDB JSON file {mongo_file.name}." in result.stdout
    ), result.stdout
    assert (
        "Detected existing structures in collection" not in result.stdout
    ), result.stdout
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_data} StructureData and CifData Nodes or MongoDB documents have been "
        "initialized." in result.stdout
    ), result.stdout

    assert n_data == len(STRUCTURES_MONGO)

    # Try again, now all Nodes should have been updated
    result = run_cli_command(cmd_init.init, options)
    assert (
        f"Initializing MongoDB JSON file {mongo_file.name}." in result.stdout
    ), result.stdout
    assert "Detected existing structures in collection" in result.stdout, result.stdout
    assert "Success:" not in result.stdout, result.stdout
    assert (
        "No new StructureData and CifData Nodes or MongoDB documents found to "
        "initialize" in result.stdout
    ), result.stdout

    assert n_data == len(STRUCTURES_MONGO)

    # Try again with --force to get "first" result again
    options.append("--force")
    result = run_cli_command(cmd_init.init, options)
    assert (
        f"Initializing MongoDB JSON file {mongo_file.name}." in result.stdout
    ), result.stdout
    assert (
        "Detected existing structures in collection" not in result.stdout
    ), result.stdout
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_data} StructureData and CifData Nodes or MongoDB documents have been "
        "initialized." in result.stdout
    ), result.stdout

    assert n_data == len(STRUCTURES_MONGO)

    # Repopulate database with the "proper" test data
    STRUCTURES_MONGO.collection.drop()
    with open(top_dir.joinpath("tests/static/test_structures_mongo.json")) as handle:
        data = bson.json_util.loads(handle.read())
    STRUCTURES_MONGO.collection.insert_many(data)
