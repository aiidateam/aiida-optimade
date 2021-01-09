# pylint: disable=protected-access
import click
from tqdm import tqdm

from aiida_optimade.cli.cmd_aiida_optimade import cli
from aiida_optimade.common.logger import disable_logging, LOGGER


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
@click.option(
    "-m",
    "--minimized-fields",
    is_flag=True,
    default=False,
    show_default=True,
    help=(
        "Do not calculate large-valued fields. This is especially good for structure "
        "with thousands of atoms."
    ),
)
@click.pass_obj
def init(obj: dict, force: bool, silent: bool, minimized_fields: bool):
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
        if minimized_fields:
            minimized_keys = (
                STRUCTURES.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
            )
            minimized_keys |= STRUCTURES.get_attribute_fields()
            minimized_keys |= {
                f"_{STRUCTURES.provider}_" + _ for _ in STRUCTURES.provider_fields
            }
            minimized_keys.difference_update(
                {"cartesian_site_positions", "nsites", "species_at_sites"}
            )
            STRUCTURES._alias_filter(dict.fromkeys(minimized_keys, None))
        else:
            STRUCTURES._alias_filter({"nsites": None})

        updated_pks = STRUCTURES._check_and_calculate_entities(
            cli=not silent, all_fields=not minimized_fields
        )
    except Exception as exc:  # pylint: disable=broad-except
        from traceback import print_exc

        LOGGER.error("Full exception from 'aiida-optimade init' CLI:\n%s", print_exc())
        echo.echo_critical(
            f"An exception happened while trying to initialize {profile!r}:\n{exc!r}"
        )

    if not silent:
        if updated_pks:
            echo.echo_success(
                f"{profile!r} has been initialized for use with AiiDA-OPTIMADE. "
                f"{len(updated_pks)} StructureData and CifData Nodes have been "
                "initialized."
            )
        else:
            echo.echo_info(
                "No new StructureData and CifData Nodes found to initialize for "
                f"{profile!r}."
            )
