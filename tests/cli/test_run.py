# pylint: disable=redefined-outer-name
import os
from multiprocessing import Process
from time import sleep
from typing import List

import pytest


@pytest.fixture
def run_server(run_cli_command, **kwargs):
    """Run the server using `aiida-optimade run`

    :param options: the list of command line options to pass to `aiida-optimade run`
        invocation
    :param raises: whether `aiida-optimade run` is expected to raise an exception
    """
    from aiida_optimade.cli import cmd_run

    try:
        kwargs["command"] = cmd_run.run
        server = Process(target=run_cli_command, kwargs=kwargs)
        server.start()
        sleep(10)  # The server needs time to start up
        yield
    finally:
        server.terminate()
        sleep(5)


@pytest.fixture
def run_and_terminate_server(run_cli_command, capfd):
    """Run server and close it again, returning click.testing.Result"""

    capfd.readouterr()  # This is supposed to clear the internal cache

    def _run_and_terminate_server(options: List[str] = None, raises: bool = False):
        """Run the server using `aiida-optimade run`

        :param options: the list of command line options to pass to `aiida-optimade run`
            invocation
        :param raises: whether `aiida-optimade run` is expected to raise an exception
        :return: sys output
        """
        from aiida_optimade.cli import cmd_run

        try:
            kwargs = {
                "command": cmd_run.run,
                "options": options,
                "raises": raises,
            }
            server = Process(target=run_cli_command, kwargs=kwargs)
            server.start()
            sleep(10)  # The server needs time to start up
            output = capfd.readouterr()
        finally:
            server.terminate()
            sleep(5)

        return output

    return _run_and_terminate_server


def test_run(run_server):  # pylint: disable=unused-argument
    """Test running `aiida-optimade run`"""
    import requests
    from optimade import __api_version__
    from optimade.models import InfoResponse

    response = requests.get(
        "http://localhost:5000"
        f"/v{__api_version__.split('-')[0].split('+')[0].split('.')[0]}"
        "/info"
    )
    assert response.status_code == 200
    response_json = response.json()
    InfoResponse(**response_json)


def test_log_level_debug(run_and_terminate_server):
    """Test passing log level "debug" to `aiida-optimade run`"""
    options = ["--log-level", "debug"]
    output = run_and_terminate_server(options=options)
    assert "DEBUG MODE" in output.out
    assert "DEBUG:" in output.out


def test_log_level_warning(run_and_terminate_server):
    """Test passing log level "warning" to `aiida-optimade run`"""
    options = ["--log-level", "warning"]
    output = run_and_terminate_server(options=options)
    assert "DEBUG MODE" not in output.out
    assert "DEBUG:" not in output.out and "DEBUG:" not in output.err


def test_non_valid_log_level(run_and_terminate_server):
    """Test passing a non-valid log level to `aiida-optimade run`"""
    options = ["--log-level", "test"]
    output = run_and_terminate_server(options=options, raises=True)
    assert not output.out
    assert not output.err


def test_debug(run_and_terminate_server):
    """Test --debug flag"""
    options = ["--debug"]
    output = run_and_terminate_server(options=options)
    assert "DEBUG MODE" in output.out
    assert "DEBUG:" in output.out


def test_logging_precedence(run_and_terminate_server):
    """Test --log-level takes precedence over --debug"""
    options = ["--debug", "--log-level", "warning"]
    output = run_and_terminate_server(options=options)
    assert "DEBUG MODE" not in output.out
    assert "DEBUG:" not in output.out and "DEBUG:" not in output.err


def test_env_var_is_set(run_and_terminate_server):
    """Test the AIIDA_PROFILE env var is set

    The issue with this test, is that the set "AIIDA_PROFILE" environment variable
    in the click command cannot be retrieved from the test functions' `os.environ`.
    Hence, we test it by making sure the current AiiDA profile is reported to be the
    active profile when running the server.

    Since `run_and_terminate_server` automatically sets the "AIIDA_PROFILE"
    environment variable to the current "AIIDA_PROFILE", we will check that here.
    """

    fixture_profile = os.getenv("AIIDA_PROFILE")
    assert fixture_profile is not None
    if fixture_profile == "test_profile":
        # This is for local tests only
        fixture_profile = "optimade_sqla"
    options = ["--debug"]
    output = run_and_terminate_server(options=options)
    assert fixture_profile in output.out
