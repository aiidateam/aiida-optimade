# pylint: disable=protected-access,too-many-statements
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
    help="Force re-calculation of all OPTIMADE fields from the AiiDA database.",
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
    "--mongo",
    is_flag=True,
    default=False,
    show_default=True,
    help=(
        "Create a MongoDB collection for the OPTIMADE fields instead of storing as a "
        "Node extra."
    ),
)
@click.pass_obj
def init(obj: dict, force: bool, silent: bool, mongo: bool):
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

            if mongo:
                from optimade.server.config import CONFIG
                from aiida_optimade.routers.structures import STRUCTURES_MONGO

        if force:
            # Remove all OPTIMADE-specific extras / dropping MongoDB collection
            if mongo:
                if not silent:
                    echo.echo_warning(
                        "Forcing re-calculation. About to drop structures collection "
                        f"{STRUCTURES_MONGO.collection.full_name!r} in MongoDB."
                    )
                STRUCTURES_MONGO.collection.drop()
                if not silent:
                    echo.echo_info(
                        f"Done dropping {STRUCTURES_MONGO.collection.full_name!r} "
                        "collection."
                    )
            else:
                extras_key = STRUCTURES.resource_mapper.PROJECT_PREFIX.split(".")[1]
                query_kwargs = {
                    "filters": {"extras": {"has_key": extras_key}},
                    "project": "*",
                }

                number_of_nodes = STRUCTURES.count(**query_kwargs)
                if not silent:
                    echo.echo_info(
                        "Forcing re-calculation. About to remove OPTIMADE-specific "
                        f"extras for {number_of_nodes} Nodes."
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
                        f"Done removing extra {extras_key!r} in {number_of_nodes} "
                        "Nodes."
                    )

        if not silent:
            echo.echo_info(f"Initializing {profile!r}.")
            echo.echo_warning("This may take several minutes!")

        if mongo:
            CONFIG.use_real_mongo = True
            entries = {_[0] for _ in STRUCTURES._find_all(project="id")}
            entries -= {
                int(_["id"])
                for _ in STRUCTURES_MONGO.collection.find(filter={}, projection=["id"])
            }
            entries = [[_] for _ in entries]

        STRUCTURES._filter_fields = {
            STRUCTURES.resource_mapper.alias_for(_)
            for _ in STRUCTURES.resource_mapper.ALL_ATTRIBUTES
        }
        updated_pks = STRUCTURES._check_and_calculate_entities(
            cli=not silent,
            entries=entries if mongo else None,
        )
    except Exception as exc:  # pylint: disable=broad-except
        import traceback

        exception = traceback.format_exc()

        LOGGER.error("Full exception from 'aiida-optimade init' CLI:\n%s", exception)
        echo.echo_critical(
            f"An exception happened while trying to initialize {profile!r} (see log "
            f"for more details):\n{exc!r}"
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
