# pylint: disable=unused-argument,too-many-locals
def test_calc_all_new(run_cli_command, aiida_profile, top_dir):
    """Test `aiida-optimade -p profile_name recalc` works for non-existent fields.

    By "non-existent" the meaning is calculating fields that don't already exist for
    any Nodes.
    """
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_recalc
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database and get initialized_structure_nodes.aiida
    aiida_profile.reset_db()
    archive = top_dir.joinpath("tests/cli/static/initialized_structure_nodes.aiida")
    import_data(archive)

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

    options = ["--force-yes"] + fields
    result = run_cli_command(cmd_recalc.recalc, options)

    assert (
        f"Fields found for {n_structure_data} Nodes." not in result.stdout
    ), result.stdout
    assert (
        f"Removing fields for {n_structure_data} Nodes." not in result.stdout
    ), result.stdout

    assert "Success:" in result.stdout, result.stdout
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
    original_data = top_dir.joinpath("tests/static/test_structures.aiida")
    import_data(original_data)


def test_calc(run_cli_command, aiida_profile, top_dir):
    """Test `aiida-optimade -p profile_name recalc` works."""
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_recalc
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database and get initialized_structure_nodes.aiida
    aiida_profile.reset_db()
    archive = top_dir.joinpath("tests/cli/static/initialized_structure_nodes.aiida")
    import_data(archive)

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

    options = ["--force-yes"] + fields
    result = run_cli_command(cmd_recalc.recalc, options)

    assert f"Fields found for {n_structure_data} Nodes." in result.stdout, result.stdout
    assert (
        f"Removing fields for {n_structure_data} Nodes." in result.stdout
    ), result.stdout

    assert "Success:" in result.stdout, result.stdout
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
    original_data = top_dir.joinpath("tests/static/test_structures.aiida")
    import_data(original_data)


def test_calc_partially_init(run_cli_command, aiida_profile, top_dir):
    """Test `aiida-optimade -p profile_name recalc` works for a partially initalized DB"""
    from aiida import orm
    from aiida.tools.importexport import import_data

    from aiida_optimade.cli import cmd_recalc
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database and get initialized_structure_nodes.aiida
    aiida_profile.reset_db()
    archive = top_dir.joinpath("tests/cli/static/initialized_structure_nodes.aiida")
    import_data(archive)

    extras_key = AiidaEntityTranslator.EXTRAS_KEY
    original_data = orm.QueryBuilder().append(
        orm.StructureData, project=["*", f"extras.{extras_key}"]
    )
    n_total_nodes = original_data.count()
    original_data = original_data.all()

    # Alter extra for various Nodes
    node, _ = original_data[0]
    node.delete_extra(extras_key)
    del node

    node, optimade = original_data[1]
    optimade.pop("elements", None)
    optimade.pop("elements_ratios", None)
    node.set_extra(extras_key, optimade)
    del node

    node, optimade = original_data[2]
    optimade.pop("elements", None)
    node.set_extra(extras_key, optimade)
    del node

    node, optimade = original_data[3]
    optimade.pop("elements_ratios", None)
    node.set_extra(extras_key, optimade)
    del node

    del original_data

    # "elements" should not be found in 3 Nodes
    options = ["--force-yes", "elements"]
    result = run_cli_command(cmd_recalc.recalc, options)

    assert f"Field found for {n_total_nodes - 3} Nodes." in result.stdout, result.stdout
    assert (
        f"Removing field for {n_total_nodes - 3} Nodes." in result.stdout
    ), result.stdout

    assert "Success:" in result.stdout, result.stdout
    assert f"calculated for {n_total_nodes} Nodes" in result.stdout, result.stdout

    n_updated_structure_data = (
        orm.QueryBuilder()
        .append(
            orm.StructureData,
            filters={f"extras.{extras_key}": {"has_key": "elements"}},
        )
        .count()
    )

    assert n_total_nodes == n_updated_structure_data

    # All missing fields should have been calcualted for all Nodes now,
    # since "elements" will have been removed from all Nodes that had it
    # first, meaning all Nodes will be investigated for other missing
    # fields automatically - always.
    # Let's check with "elements_ratios", which was the only field removed
    # from one Node above.
    # This will also test if "elements_ratios" will be calculated from a
    # Node where both it and "elements" were missing prior to the previous
    # invocation of `aiida-optimade recalc`.
    n_structure_data = (
        orm.QueryBuilder()
        .append(
            orm.StructureData,
            filters={f"extras.{extras_key}": {"has_key": "elements_ratios"}},
        )
        .count()
    )
    assert n_structure_data == n_total_nodes

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structures.aiida")
    import_data(original_data)
