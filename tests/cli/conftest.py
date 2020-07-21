"""Pytest fixtures for command line interface tests."""
import os
from typing import List

import click
import pytest


@pytest.fixture
def run_cli_command():
    """Run a `click` command with the given options.

    The call will raise if the command triggered an exception or the exit code returned
    is non-zero.
    """
    from click.testing import Result

    def _run_cli_command(
        command: click.Command, options: List[str] = None, raises: bool = False
    ) -> Result:
        """Run the command and check the result.

        Note, the `output_lines` attribute is added to return value containing list of
        stripped output lines.

        :param options: the list of command line options to pass to the command
            invocation
        :param raises: whether the command is expected to raise an exception
        :return: test result
        """
        import traceback

        runner = click.testing.CliRunner()
        profile = os.getenv("AIIDA_PROFILE", "optimade_sqla")
        if profile == "test_profile":
            # This is for local tests only
            profile = "optimade_sqla"
        result = runner.invoke(command, options or [], env={"AIIDA_PROFILE": profile})

        if raises:
            assert result.exception is not None, result.output
            assert result.exit_code != 0
        else:
            assert result.exception is None, "".join(
                traceback.format_exception(*result.exc_info)
            )
            assert result.exit_code == 0, result.output

        result.output_lines = [
            line.strip() for line in result.output.split("\n") if line.strip()
        ]

        return result

    return _run_cli_command
