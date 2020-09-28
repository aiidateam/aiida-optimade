import os
from pathlib import Path

import click

from aiida.cmdline.params.options import PROFILE as VERDI_PROFILE
from aiida.cmdline.params.types import ProfileParamType as VerdiProfileParamType
from aiida.manage.configuration import Profile

from aiida_optimade.cli.options import AIIDA_PROFILES


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(
    None, "-v", "--version", message="AiiDA-OPTIMADE version %(version)s"
)
@VERDI_PROFILE(
    type=VerdiProfileParamType(),
    default="optimade_sqla",
    show_default=True,
    help="AiiDA profile to use and serve. Configured profiles: "
    f"{', '.join([repr(name) for name in AIIDA_PROFILES])}.",
)
@click.pass_context
def cli(ctx, profile: Profile):  # pragma: no cover
    """AiiDA-OPTIMADE command line interface (CLI)."""

    if ctx.obj is None:
        ctx.obj = {}

    ctx.obj["profile"] = profile

    # Set config
    if (
        not os.getenv("OPTIMADE_CONFIG_FILE")
        or not Path(os.getenv("OPTIMADE_CONFIG_FILE")).exists()
    ):
        os.environ["OPTIMADE_CONFIG_FILE"] = str(
            Path(__file__).parent.parent.joinpath("config.json").resolve()
        )
