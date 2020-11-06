# pylint: disable=protected-access,too-many-locals
from typing import Tuple

import click

from aiida_optimade.cli.cmd_aiida_optimade import cli
from aiida_optimade.common.logger import LOGGER


@cli.command()
@click.argument(
    "fields",
    type=click.STRING,
    required=True,
    nargs=-1,
)
@click.option(
    "-y",
    "--force-yes",
    is_flag=True,
    default=False,
    show_default=True,
    help=(
        "Do not ask for confirmation when (re-)calculating the OPTIMADE field(s) in "
        "the AiiDA database."
    ),
)
@click.option(
    "-q",
    "--silent",
    is_flag=True,
    default=False,
    show_default=True,
    help="Suppress informational output.",
)
@click.pass_obj
def calc(obj: dict, fields: Tuple[str], force_yes: bool, silent: bool):
    """Calculate OPTIMADE fields in the AiiDA database."""
    from aiida import load_profile

    try:
        profile: str = obj.get("profile").name
    except AttributeError:
        profile = None
    profile = load_profile(profile).name

    try:
        from aiida_optimade.routers.structures import STRUCTURES

        if not force_yes:
            click.confirm(
                "Are you sure you want to (re-)calculate the field(s): "
                f"{', '.join(fields)}?",
                default=True,
                abort=True,
                show_default=True,
            )

        # Remove OPTIMADE fields in OPTIMADE-specific extra
        extras_key = STRUCTURES.resource_mapper.PROJECT_PREFIX.split(".")[1]
        query_kwargs = {
            "filters": {
                "and": [
                    {"extras": {"has_key": extras_key}},
                    {
                        f"extras.{extras_key}": {
                            "or": [{"has_key": field} for field in fields]
                        }
                    },
                ]
            },
            "project": ["*", "extras.optimade"],
        }

        number_of_nodes = STRUCTURES.count(**query_kwargs)
        if number_of_nodes:
            if not silent:
                click.echo(
                    f"Fields found for {number_of_nodes} Nodes. "
                    "The fields will now be removed for these Nodes. "
                    "Note: This may take several minutes!"
                )

            all_calculated_nodes = STRUCTURES._find_all(**query_kwargs)
            for node, optimade in all_calculated_nodes:
                for field in fields:
                    optimade.pop(field, None)
                node.set_extra("optimade", optimade)
                del node
            del all_calculated_nodes

            if not silent:
                click.echo(
                    f"Done removing {', '.join(fields)} from {number_of_nodes} Nodes."
                )

        if not silent:
            click.echo(
                f"{'Re-c' if number_of_nodes else 'C'}alcuating field(s) {fields} in "
                f"{profile!r}. Note: This may take several minutes!"
            )

        STRUCTURES._filter_fields = set()
        STRUCTURES._alias_filter({field: "" for field in fields})
        updated_pks = STRUCTURES._check_and_calculate_entities()
    except click.Abort:
        click.echo("Aborted!")
        return
    except Exception as exc:  # pylint: disable=broad-except
        from traceback import print_exc

        LOGGER.error("Full exception from 'aiida-optimade calc' CLI:\n%s", print_exc())
        click.echo(
            f"An exception happened while trying to initialize {profile!r}:\n{exc!r}"
        )
        return

    if not silent:
        if updated_pks:
            click.echo(
                f"Success! {profile!r} has had {len(fields)} fields calculated for "
                f"{len(updated_pks)} Nodes for use with AiiDA-OPTIMADE."
            )
        else:
            click.echo(
                f"No StructureData Nodes found to calculate fields {', '.join(fields)} for "
                f"{profile!r}."
            )
