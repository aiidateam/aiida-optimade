# pylint: disable=protected-access
import click

from aiida_optimade.cli.cmd_aiida_optimade import cli


@cli.command()
@click.pass_obj
def init(obj: dict):
    """Initialize an AiiDA database to be served with AiiDA-OPTIMADE."""
    from aiida import load_profile

    try:
        profile: str = obj.get("profile").name
    except AttributeError:
        profile = None
    profile = load_profile(profile).name

    try:
        from aiida_optimade.routers.structures import STRUCTURES

        click.echo(f"Initializing {profile!r}. Note: This may take several minutes!")

        STRUCTURES._filter_fields = set()
        STRUCTURES._alias_filter({"nelements": "2"})
        updated_pks = STRUCTURES._check_and_calculate_entities()
    except Exception as exc:  # pylint: disable=broad-except
        click.echo(
            f"An exception ({exc.__class__.__name__}) happened while trying to "
            f"initialize {profile!r}:\n{exc}"
        )
        return

    if updated_pks:
        click.echo(
            f"Success! {profile!r} has been initialized for use with AiiDA-OPTIMADE."
        )
        click.echo(f"{len(updated_pks)} StructureData Nodes have been initialized.")
    else:
        click.echo(f"No new StructureData Nodes found to initialize for {profile!r}.")
