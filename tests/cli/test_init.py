def test_init_structuredata(run_cli_command, aiida_profile, top_dir):
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

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structuredata.aiida")
    import_data(original_data)


def test_init_cifdata(run_cli_command, aiida_profile, top_dir):
    """Test `aiida-optimade -p profile_name init` works for CifData Nodes."""
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_init
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database
    aiida_profile.reset_db()

    archive = top_dir.joinpath("tests/cli/static/cif_data_nodes.aiida")
    import_data(archive)

    n_structure_data = orm.QueryBuilder().append(orm.CifData).count()

    result = run_cli_command(cmd_init.init)
    assert "Success:" in result.stdout, result.stdout
    assert (
        f"{n_structure_data} StructureData and CifData Nodes have been initialized."
        in result.stdout
    ), result.stdout

    extras_key = AiidaEntityTranslator.EXTRAS_KEY
    n_updated_structure_data = (
        orm.QueryBuilder()
        .append(orm.CifData, filters={"extras": {"has_key": extras_key}})
        .count()
    )
    assert n_structure_data == n_updated_structure_data

    # Try again, now all Nodes should have been updated
    result = run_cli_command(cmd_init.init)
    assert "No new StructureData and CifData Nodes found to initialize" in result.stdout

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structuredata.aiida")
    import_data(original_data)
