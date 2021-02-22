# pylint: disable=protected-access,too-many-locals,too-many-branches
from typing import Tuple

import click
from tqdm import tqdm

from aiida_optimade.cli.cmd_aiida_optimade import cli
from aiida_optimade.common.logger import LOGGER, disable_logging


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
    from aiida.cmdline.utils import echo

    try:
        profile: str = obj.get("profile").name
    except AttributeError:
        profile = None
    profile = load_profile(profile).name

    try:
        with disable_logging():
            from aiida_optimade.routers.structures import STRUCTURES

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
                echo.echo_info(
                    f"Field{'s' if len(fields) > 1 else ''} found for {number_of_nodes}"
                    f" Node{'s' if number_of_nodes > 1 else ''}."
                )
        if not silent:
            echo.echo_info(
                f"Total number of Nodes in profile {profile!r}: {STRUCTURES.count()}"
            )

        if not force_yes:
            click.confirm(
                f"Are you sure you want to {'re-' if number_of_nodes else ''}"
                f"calculate the field{'s' if len(fields) > 1 else ''}: "
                f"{', '.join(fields)}?",
                default=True,
                abort=True,
                show_default=True,
            )

        if number_of_nodes:
            if not silent:
                echo.echo_warning(
                    f"Removing field{'s' if len(fields) > 1 else ''} for "
                    f"{number_of_nodes} Node{'s' if number_of_nodes > 1 else ''}. "
                    "This may take several minutes!"
                )

            all_calculated_nodes = STRUCTURES._find_all(**query_kwargs)

            if not silent:
                all_calculated_nodes = tqdm(
                    all_calculated_nodes, desc="Removing fields", leave=False
                )

            for node, optimade in all_calculated_nodes:
                for field in fields:
                    optimade.pop(field, None)
                node.set_extra("optimade", optimade)
                del node
            del all_calculated_nodes

            if not silent:
                echo.echo_info(
                    f"Done removing {', '.join(fields)} from {number_of_nodes} Node"
                    f"{'s' if number_of_nodes > 1 else ''}."
                )

        if not silent:
            echo.echo_warning(
                f"Calcuating field{'s' if len(fields) > 1 else ''} {', '.join(fields)}."
                " This may take several minutes!"
            )

        STRUCTURES._filter_fields = {
            STRUCTURES.resource_mapper.alias_for(_) for _ in fields
        }
        updated_pks = STRUCTURES._check_and_calculate_entities(cli=not silent)
    except click.Abort:
        echo.echo_warning("Aborted!")
        return
    except Exception as exc:  # pylint: disable=broad-except
        import traceback

        exception = traceback.format_exc()

        LOGGER.error("Full exception from 'aiida-optimade calc' CLI:\n%s", exception)
        echo.echo_critical(
            f"An exception happened while trying to initialize {profile!r} (see log "
            f"for more details):\n{exc!r}"
        )

    if not silent:
        if updated_pks:
            echo.echo_success(
                f"{profile!r} has had {len(fields)} field"
                f"{'s' if len(fields) > 1 else ''} calculated for {len(updated_pks)} "
                f"Node{'s' if len(updated_pks) > 1 else ''} for use with "
                "AiiDA-OPTIMADE."
            )
        else:
            echo.echo_info(
                "No StructureData and CifData Nodes found to calculate field"
                f"{'s' if len(fields) > 1 else ''} {', '.join(fields)} for {profile!r}."
            )
