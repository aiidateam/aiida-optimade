# pylint: disable=unused-argument,too-many-locals
def test_calc_all_new(run_cli_command, aiida_profile, top_dir):
    """Test `aiida-optimade -p profile_name calc` works for non-existant fields.

    By "non-existant" the meaning is calculating fields that don't already exist for
    any Nodes.
    """
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_calc
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database and get initialized_nodes.aiida
    aiida_profile.reset_db()
    archive = top_dir.joinpath("tests/cli/static/initialized_nodes.aiida")
    import_data(archive, silent=True)

    fields = ["elements", "chemical_formula_hill"]

    extras_key = AiidaEntityTranslator.EXTRAS_KEY
    original_data = (
        orm.QueryBuilder()
        .append(
            orm.StructureData,
            filters={
                f"extras.{extras_key}": {"or": [{"has_key": field} for field in fields]}
            },
            project=["*", f"extras.{extras_key}"],
        )
        .all()
    )

    # Remove these fields
    for node, optimade in original_data:
        for field in fields:
            optimade.pop(field, None)
        node.set_extra(extras_key, optimade)
        del node
    del original_data

    n_structure_data = (
        orm.QueryBuilder()
        .append(
            orm.StructureData,
            filters={
                f"extras.{extras_key}": {
                    "or": [{"!has_key": field} for field in fields]
                }
            },
        )
        .count()
    )

    options = ["--silent"] + fields
    result = run_cli_command(cmd_calc.calc, options)

    assert (
        f"Fields found for {n_structure_data} Nodes." not in result.stdout
    ), result.stdout
    assert (
        "The fields will now be removed for these Nodes." not in result.stdout
    ), result.stdout

    assert "Success!" in result.stdout, result.stdout
    assert f"calculated for {n_structure_data} Nodes" in result.stdout, result.stdout

    n_updated_structure_data = (
        orm.QueryBuilder()
        .append(
            orm.StructureData,
            filters={
                f"extras.{extras_key}": {"or": [{"has_key": field} for field in fields]}
            },
        )
        .count()
    )

    assert n_structure_data == n_updated_structure_data

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structuredata.aiida")
    import_data(original_data, silent=True)


def test_calc(run_cli_command, aiida_profile, top_dir):
    """Test `aiida-optimade -p profile_name calc` works."""
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_calc
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database and get initialized_nodes.aiida
    aiida_profile.reset_db()
    archive = top_dir.joinpath("tests/cli/static/initialized_nodes.aiida")
    import_data(archive, silent=True)

    fields = ["elements", "chemical_formula_hill"]

    extras_key = AiidaEntityTranslator.EXTRAS_KEY

    n_structure_data = (
        orm.QueryBuilder()
        .append(
            orm.StructureData,
            filters={
                f"extras.{extras_key}": {"or": [{"has_key": field} for field in fields]}
            },
        )
        .count()
    )

    options = ["--silent"] + fields
    result = run_cli_command(cmd_calc.calc, options)

    assert f"Fields found for {n_structure_data} Nodes." in result.stdout, result.stdout
    assert (
        "The fields will now be removed for these Nodes." in result.stdout
    ), result.stdout

    assert "Success!" in result.stdout, result.stdout
    assert f"calculated for {n_structure_data} Nodes" in result.stdout, result.stdout

    n_updated_structure_data = (
        orm.QueryBuilder()
        .append(
            orm.StructureData,
            filters={
                f"extras.{extras_key}": {"or": [{"has_key": field} for field in fields]}
            },
        )
        .count()
    )

    assert n_structure_data == n_updated_structure_data

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structuredata.aiida")
    import_data(original_data, silent=True)
