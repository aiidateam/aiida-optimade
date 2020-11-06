# pylint: disable=too-many-arguments
import click

from aiida_optimade.cli.cmd_aiida_optimade import cli
from aiida_optimade.cli.options import LOGGING_LEVELS


@cli.command()
@click.option(
    "--log-level",
    type=click.Choice(LOGGING_LEVELS, case_sensitive=False),
    default="info",
    show_default=True,
    help="Set the log-level of the server.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    show_default=True,
    help="Will set the log-level to DEBUG. Note, parameter log-level takes precedence "
    "if not 'info'!",
)
@click.option(
    "--host",
    type=click.STRING,
    default="127.0.0.1",
    show_default=True,
    help="Bind socket to this host.",
)
@click.option(
    "--port",
    type=click.INT,
    default=5000,
    show_default=True,
    help="Bind socket to this port.",
)
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    show_default=True,
    help="Enable auto-reload. Note, if --debug is set, this will also be set to True.",
)
@click.pass_obj
def run(obj: dict, log_level: str, debug: bool, host: str, port: int, reload: bool):
    """Run AiiDA-OPTIMADE server."""
    import os
    import uvicorn

    log_level = log_level.lower()
    if debug and log_level == "info":
        log_level = "debug"

    if debug and not reload:
        reload = True

    if log_level == "debug":
        os.environ["OPTIMADE_DEBUG"] = "1"
    else:
        os.environ["OPTIMADE_DEBUG"] = "0"

    os.environ["AIIDA_OPTIMADE_LOG_LEVEL"] = log_level.upper()

    if os.getenv("AIIDA_PROFILE") is None:
        from aiida import load_profile

        try:
            profile: str = obj.get("profile").name
        except AttributeError:
            profile = None
        profile_name: str = load_profile(profile).name
        os.environ["AIIDA_PROFILE"] = profile_name

    uvicorn.run(
        "aiida_optimade.main:APP",
        reload=reload,
        host=host,
        port=port,
        log_level=log_level,
        debug=debug,
    )
