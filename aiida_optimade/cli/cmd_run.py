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
@click.pass_obj
def run(obj: dict, log_level: str, debug: bool):
    """Run AiiDA-OPTIMADE server."""
    import os
    import uvicorn

    log_level = log_level.lower()
    if debug and log_level == "info":
        log_level = "debug"

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

    uvicorn.run("aiida_optimade.main:APP", reload=True, port=5000, log_level=log_level)
