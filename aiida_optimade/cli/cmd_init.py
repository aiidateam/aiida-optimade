# pylint: disable=protected-access
import click

from aiida_optimade.cli.cmd_aiida_optimade import cli


@cli.command()
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    show_default=True,
    help="Force re-calculation of all OPTIMADE fields in the AiiDA database.",
)
@click.pass_obj
def init(obj: dict, force: bool):
    """Initialize an AiiDA database to be served with AiiDA-OPTIMADE."""
    from aiida import load_profile

    try:
        profile: str = obj.get("profile").name
    except AttributeError:
        profile = None
    profile = load_profile(profile).name

    try:
        from aiida_optimade.routers.structures import STRUCTURES

        if force:
            # Remove all OPTIMADE-specific extras
            extras_key = STRUCTURES.resource_mapper.PROJECT_PREFIX.split(".")[1]
            query_kwargs = {
                "filters": {"extras": {"has_key": extras_key}},
                "project": "*",
            }

            number_of_nodes = STRUCTURES.count(**query_kwargs)
            click.echo(
                "Forcing re-calculation. About to remove OPTIMADE-specific extras for "
                f"{number_of_nodes} Nodes. Note: This may take several seconds!"
            )

            all_calculated_nodes = STRUCTURES._find_all(**query_kwargs)
            for (node,) in all_calculated_nodes:
                node.delete_extra(extras_key)

            click.echo(
                f"Done removing extra {extras_key!r} in {number_of_nodes} Nodes."
            )

        click.echo(f"Initializing {profile!r}. Note: This may take several minutes!")

        STRUCTURES._filter_fields = set()
        STRUCTURES._alias_filter({"nelements": "2"})
        updated_pks = STRUCTURES._check_and_calculate_entities()
    except Exception as exc:  # pylint: disable=broad-except
        click.echo(
            f"An exception happened while trying to initialize {profile!r}:\n{exc!r}"
        )
        return

    if updated_pks:
        click.echo(
            f"Success! {profile!r} has been initialized for use with AiiDA-OPTIMADE."
        )
        click.echo(f"{len(updated_pks)} StructureData Nodes have been initialized.")
    else:
        click.echo(f"No new StructureData Nodes found to initialize for {profile!r}.")
