"""Pytest fixtures for command line interface tests."""
# pylint: disable=redefined-outer-name,import-error
import os
import signal
from subprocess import PIPE, Popen, TimeoutExpired
from time import sleep

import click
import pytest


@pytest.fixture
def aiida_test_profile() -> str:
    """Return AiiDA test profile used for AiiDA-OPTIMADE"""
    from aiida_optimade.cli.cmd_aiida_optimade import AIIDA_OPTIMADE_TEST_PROFILE

    return AIIDA_OPTIMADE_TEST_PROFILE


@pytest.fixture
def run_cli_command(aiida_test_profile: str):
    """Run a `click` command with the given options.

    The call will raise if the command triggered an exception or the exit code returned
    is non-zero.
    """
    from click.testing import Result

    def _run_cli_command(
        command: click.Command, options: list[str] = None, raises: bool = False
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
        profile = os.getenv("AIIDA_PROFILE", aiida_test_profile)
        if profile == "test_profile":
            # This is for local tests only
            profile = aiida_test_profile
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


@pytest.fixture
def run_and_terminate_server(aiida_test_profile: str):
    """Run a `click` command with the given options.

    The call will raise if the command triggered an exception or the exit code returned
    is non-zero.
    """

    def _run_and_terminate_server(
        command: str, options: list[str] = None
    ) -> tuple[str, str]:
        """Run the command and check the result.

        Note, the `output_lines` attribute is added to return value containing list of
        stripped output lines.

        :param command: `aiida-optimade` command to use.
        :param options: The list of command line options to pass to the command
            invocation
        :param raises: Whether the command is expected to raise an exception
        :return: Test result
        """
        profile = os.getenv("AIIDA_PROFILE", aiida_test_profile)
        if profile == "test_profile":
            # This is for local tests only
            profile = aiida_test_profile

        args = ["aiida-optimade", "-p", profile]
        args.append(command)
        args.extend(options or [])

        env = dict(os.environ)
        env["AIIDA_PROFILE"] = profile
        result = Popen(args, env=env, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        sleep(10)  # The server needs time to start up

        result.send_signal(signal.SIGINT)
        try:
            result.wait(10)
        except TimeoutExpired:
            result.kill()
            sleep(2)

        stdout, stderr = result.communicate()

        assert result is not None

        return stdout, stderr

    return _run_and_terminate_server
