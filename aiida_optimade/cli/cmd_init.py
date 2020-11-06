# pylint: disable=protected-access
import click
from tqdm import tqdm

from aiida_optimade.cli.cmd_aiida_optimade import cli
from aiida_optimade.common.logger import disable_logging


@cli.command()
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    show_default=True,
    help="Force re-calculation of all OPTIMADE fields in the AiiDA database.",
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
def init(obj: dict, force: bool, silent: bool):
    """Initialize an AiiDA database to be served with AiiDA-OPTIMADE."""
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

        if force:
            # Remove all OPTIMADE-specific extras
            extras_key = STRUCTURES.resource_mapper.PROJECT_PREFIX.split(".")[1]
            query_kwargs = {
                "filters": {"extras": {"has_key": extras_key}},
                "project": "*",
            }

            number_of_nodes = STRUCTURES.count(**query_kwargs)
            if not silent:
                echo.echo_info(
                    "Forcing re-calculation. About to remove OPTIMADE-specific extras "
                    f"for {number_of_nodes} Nodes."
                )
                echo.echo_warning("This may take several seconds!")

            all_calculated_nodes = STRUCTURES._find_all(**query_kwargs)

            if not silent:
                all_calculated_nodes = tqdm(
                    all_calculated_nodes,
                    desc=f"Removing {extras_key!r} extras",
                    leave=False,
                )

            for (node,) in all_calculated_nodes:
                node.delete_extra(extras_key)
                del node
            del all_calculated_nodes

            if not silent:
                echo.echo_info(
                    f"Done removing extra {extras_key!r} in {number_of_nodes} Nodes."
                )

        if not silent:
            echo.echo_info(f"Initializing {profile!r}.")
            echo.echo_warning("This may take several minutes!")

        STRUCTURES._filter_fields = set()
        STRUCTURES._alias_filter({"nelements": "2"})
        updated_pks = STRUCTURES._check_and_calculate_entities(cli=not silent)
    except Exception as exc:  # pylint: disable=broad-except
        echo.echo_critical(
            f"An exception happened while trying to initialize {profile!r}:\n{exc!r}"
        )

    if not silent:
        if updated_pks:
            echo.echo_success(
                f"{profile!r} has been initialized for use with AiiDA-OPTIMADE. "
                f"{len(updated_pks)} StructureData Nodes have been initialized."
            )
        else:
            echo.echo_info(
                f"No new StructureData Nodes found to initialize for {profile!r}."
            )
