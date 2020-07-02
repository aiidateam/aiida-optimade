# pylint: disable=unused-argument
def test_init(run_cli_command, aiida_profile, top_dir):
    """Test `aiida-optimade -p profile_name init` works"""
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_init
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database
    aiida_profile.reset_db()

    archive = top_dir.joinpath("tests/cli/static/structure_data_nodes.aiida")
    import_data(archive, silent=True)

    n_structure_data = orm.QueryBuilder().append(orm.StructureData).count()

    result = run_cli_command(cmd_init.init)
    assert "Success!" in result.stdout
    assert (
        f"{n_structure_data} StructureData Nodes have been initialized."
        in result.stdout
    )

    extras_key = AiidaEntityTranslator.EXTRAS_KEY
    n_updated_structure_data = (
        orm.QueryBuilder()
        .append(orm.StructureData, filters={"extras": {"has_key": extras_key}})
        .count()
    )
    assert n_structure_data == n_updated_structure_data

    # Try again, now all Nodes should have been updated
    result = run_cli_command(cmd_init.init)
    assert "No new StructureData Nodes found to initialize" in result.stdout

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structuredata.aiida")
    import_data(original_data, silent=True)
