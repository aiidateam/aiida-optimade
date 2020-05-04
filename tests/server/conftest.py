# pylint: disable=redefined-outer-name
import pytest

from optimade.server.config import CONFIG


@pytest.fixture(scope="session")
def client():
    """Return TestClient for OPTIMADE server"""
    from fastapi.testclient import TestClient

    from aiida_optimade.main import APP
    from aiida_optimade.routers import info, structures

    # We need to remove the version prefixes in order to have the tests run correctly.
    APP.include_router(info.ROUTER)
    APP.include_router(structures.ROUTER)
    # need to explicitly set base_url, as the default "http://testserver"
    # does not validate as pydantic AnyUrl model
    return TestClient(APP, base_url="http://example.org/v0")


@pytest.fixture
def get_good_response(client):
    """Get OPTIMADE response with some sanity checks"""

    def inner(request):
        try:
            response = client.get(request)
            assert response.status_code == 200, f"Request failed: {response.json()}"
            response = response.json()
        except Exception as exc:
            print("Request attempted:")
            print(f"{client.base_url}{client.version}{request}")
            raise exc
        else:
            return response

    return inner


@pytest.fixture
def check_response(get_good_response):
    """Fixture to check response using client fixture"""

    def inner(request, expected_id, page_limit=CONFIG.page_limit):
        response = get_good_response(request=request)

        response_ids = [struct["id"] for struct in response["data"]]
        assert response["meta"]["data_returned"] == len(expected_id)
        if len(expected_id) > page_limit:
            assert expected_id[:page_limit] == response_ids
        else:
            assert expected_id == response_ids

    return inner


@pytest.fixture
def check_error_response(client):
    """General method for testing expected errornous response"""

    def inner(
        request: str,
        expected_status: int = None,
        expected_title: str = None,
        expected_detail: str = None,
    ):
        response = None
        try:
            response = client.get(request)
            assert response.status_code == expected_status, (
                "Request should have been an error with status code "
                f"{expected_status}, but instead {response.status_code} was received."
                f"\nResponse:\n{response.json()}",
            )

            response = response.json()
            assert len(response["errors"]) == 1, response.get(
                "errors", "'errors' not found"
            )
            assert response["meta"]["data_returned"] == 0, response.get(
                "meta", "'meta' not found"
            )

            error = response["errors"][0]
            assert str(expected_status) == error["status"], error
            assert expected_title == error["title"], error

            if expected_detail is None:
                expected_detail = "Error trying to process rule "
                assert error["detail"].startswith(expected_detail), error
            else:
                assert expected_detail == error["detail"], error

        except Exception as exc:
            print("Request attempted:")
            print(f"{client.base_url}{client.version}{request}")
            if response:
                print(f"\nCaptured response:\n{response}")
            raise exc

    return inner
