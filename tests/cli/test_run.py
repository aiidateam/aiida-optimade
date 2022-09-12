# pylint: disable=redefined-outer-name,unused-argument
import json
import os
import signal
from subprocess import Popen, PIPE, TimeoutExpired
from time import sleep

import pytest
import requests


@pytest.fixture
def run_server(aiida_test_profile: str):
    """Run the server using `aiida-optimade run`

    :param options: the list of command line options to pass to `aiida-optimade run`
        invocation
    :param raises: whether `aiida-optimade run` is expected to raise an exception
    """
    profile = os.getenv("AIIDA_PROFILE", aiida_test_profile)
    if profile == "test_profile":
        # This is for local tests only
        profile = aiida_test_profile

    args = ["aiida-optimade", "-p", profile, "run"]
    env = dict(os.environ)
    env["AIIDA_PROFILE"] = profile

    result = None
    try:
        result = Popen(args, env=env, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        sleep(10)  # The server needs time to start up
        yield
    finally:
        result.send_signal(signal.SIGINT)
        try:
            result.wait(10)
        except TimeoutExpired:
            result.kill()
            sleep(2)
        assert result is not None


@pytest.mark.usefixtures("run_server")
def test_run():
    """Test running `aiida-optimade run`"""
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
    """Test passing log level "debug" to `aiida-optimade run`

    In the latest versions of uvicorn, setting the log-level to "debug"
    is not enough to create debug log messages in stdout.
    One needs to also be in debug mode, i.e., either set `reload=True`
    or set `debug=True`.
    """
    options = ["--log-level", "debug"]
    output, errors = run_and_terminate_server(command="run", options=options)
    assert "DEBUG MODE" in output, f"output: {output!r}, errors: {errors!r}"
    assert "DEBUG:" not in output, f"output: {output!r}, errors: {errors!r}"


def test_log_level_warning(run_and_terminate_server):
    """Test passing log level "warning" to `aiida-optimade run`"""
    options = ["--log-level", "warning"]
    output, errors = run_and_terminate_server(command="run", options=options)
    assert "DEBUG MODE" not in output, f"output: {output!r}, errors: {errors!r}"
    assert (
        "DEBUG:" not in output and "DEBUG:" not in errors
    ), f"output: {output!r}, errors: {errors!r}"


def test_non_valid_log_level(run_and_terminate_server):
    """Test passing a non-valid log level to `aiida-optimade run`"""
    options = ["--log-level", "novalidloglevel"]
    output, errors = run_and_terminate_server(command="run", options=options)
    assert not output, f"output: {output!r}, errors: {errors!r}"
    assert (
        "Invalid value for '--log-level': 'novalidloglevel' is not one of" in errors
    ), f"output: {output!r}, errors: {errors!r}"


@pytest.mark.skip(
    "Cannot handle reloading the server with the run_and_terminate_server fixture."
)
def test_debug(run_and_terminate_server):
    """Test --debug flag"""
    options = ["--debug"]
    output, errors = run_and_terminate_server(command="run", options=options)
    assert "DEBUG MODE" in output, f"output: {output!r}, errors: {errors!r}"
    assert "DEBUG:" in output, f"output: {output!r}, errors: {errors!r}"


@pytest.mark.skip(
    "Cannot handle reloading the server with the run_and_terminate_server fixture."
)
def test_logging_precedence(run_and_terminate_server):
    """Test --log-level takes precedence over --debug"""
    options = ["--debug", "--log-level", "warning"]
    output, errors = run_and_terminate_server(command="run", options=options)
    assert "DEBUG MODE" not in output, f"output: {output!r}, errors: {errors!r}"
    assert (
        "DEBUG:" not in output and "DEBUG:" not in errors
    ), f"output: {output!r}, errors: {errors!r}"


def test_env_var_is_set(run_and_terminate_server, aiida_test_profile: str):
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
        fixture_profile = aiida_test_profile
    output, errors = run_and_terminate_server(command="run")
    assert fixture_profile in output, f"output: {output!r}, errors: {errors!r}"


@pytest.mark.usefixtures("run_server")
def test_last_modified():
    """Ensure last_modified does not change upon requests"""
    from optimade import __api_version__

    request = (
        "http://localhost:5000"
        f"/v{__api_version__.split('-')[0].split('+')[0].split('.')[0]}/structures"
    )

    first_response = requests.get(request)
    assert first_response.status_code == 200, json.dumps(
        first_response.json(), indent=2
    )
    first_response = first_response.json()
    sleep(2)
    second_response = requests.get(request)
    assert second_response.status_code == 200, json.dumps(
        second_response.json(), indent=2
    )
    second_response = second_response.json()

    assert [_["id"] for _ in first_response["data"]] == [
        _["id"] for _ in second_response["data"]
    ]
    assert [_["attributes"]["last_modified"] for _ in first_response["data"]] == [
        _["attributes"]["last_modified"] for _ in second_response["data"]
    ]


@pytest.mark.skip(
    "Cannot handle reloading the server with the run_and_terminate_server fixture."
)
def test_dev_option(run_and_terminate_server):
    """Test --dev flag

    This should be equivalent to running with the `--debug` option for
    `aiida-optimade run`, however, the profile should also be fixed to
    `aiida-optimade_test`.
    """
    options = ["--dev"]
    output, errors = run_and_terminate_server(command="run", options=options)
    assert "DEBUG MODE" in output, f"output: {output!r}, errors: {errors!r}"
    assert "DEBUG:" in output, f"output: {output!r}, errors: {errors!r}"
