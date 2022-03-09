"""Test CLI `aiida-optimade calc` command"""
# pylint: disable=unused-argument,too-many-locals,import-error
import os
import re

import pytest


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is not None,
    reason="Test is not for MongoDB",
)
def test_calc_all_new(run_cli_command, aiida_profile, top_dir, caplog):
    """Test `aiida-optimade -p profile_name calc` works for non-existent fields.

    By "non-existent" the meaning is calculating fields that don't already exist for
    any Nodes.
    """
    from aiida import orm
    from aiida.tools.archive.imports import import_archive

    from aiida_optimade.cli import cmd_calc
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database and get initialized_structure_nodes.aiida
    aiida_profile.reset_db()
    archive = top_dir.joinpath("tests/cli/static/initialized_structure_nodes.aiida")
    import_archive(archive)

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
    result = run_cli_command(cmd_calc.calc, options)

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

    # Ensure the database was reported to be updated.
    assert (
        re.match(r".*Updating Node [0-9]+ in AiiDA DB!.*", caplog.text, flags=re.DOTALL)
        is not None
    ), caplog.text

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structures.aiida")
    import_archive(original_data)


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is not None,
    reason="Test is not for MongoDB",
)
def test_calc(run_cli_command, aiida_profile, top_dir):
    """Test `aiida-optimade -p profile_name calc` works."""
    from aiida import orm
    from aiida.tools.archive.imports import import_archive

    from aiida_optimade.cli import cmd_calc
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database and get initialized_structure_nodes.aiida
    aiida_profile.reset_db()
    archive = top_dir.joinpath("tests/cli/static/initialized_structure_nodes.aiida")
    import_archive(archive)

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
    result = run_cli_command(cmd_calc.calc, options)

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
    import_archive(original_data)


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is not None,
    reason="Test is not for MongoDB",
)
def test_calc_partially_init(run_cli_command, aiida_profile, top_dir, caplog):
    """Test `aiida-optimade -p profile_name calc` works for a partially initalized DB"""
    from aiida import orm
    from aiida.tools.archive.imports import import_archive

    from aiida_optimade.cli import cmd_calc
    from aiida_optimade.translators.entities import AiidaEntityTranslator

    # Clear database and get initialized_structure_nodes.aiida
    aiida_profile.reset_db()
    archive = top_dir.joinpath("tests/cli/static/initialized_structure_nodes.aiida")
    import_archive(archive)

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
    result = run_cli_command(cmd_calc.calc, options)

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

    # Only the requested fields should have been calculated now.
    # Let's check with "elements_ratios", which was removed from the extras,
    # but wasn't re-calculated.
    # The 3 Nodes where "elements_ratios" has been removed, should still have
    # it removed now.
    n_special_structure_data = (
        orm.QueryBuilder()
        .append(
            orm.StructureData,
            filters={f"extras.{extras_key}": {"has_key": "elements_ratios"}},
        )
        .count()
    )
    assert n_special_structure_data == n_total_nodes - 3

    # Ensure the database was reported to be updated.
    assert (
        re.match(r".*Updating Node [0-9]+ in AiiDA DB!.*", caplog.text, flags=re.DOTALL)
        is not None
    ), caplog.text

    # Repopulate database with the "proper" test data
    aiida_profile.reset_db()
    original_data = top_dir.joinpath("tests/static/test_structures.aiida")
    import_archive(original_data)
