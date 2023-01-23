# pylint: disable=redefined-outer-name
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Iterable, List, Optional, Union

    from httpx import Response

    from .utils import OptimadeTestClient


@pytest.fixture(scope="module")
def client() -> "OptimadeTestClient":
    """Return TestClient for OPTIMADE server"""
    from .utils import client_factory

    return client_factory()(None, True)


@pytest.fixture(scope="module")
def remote_client() -> "OptimadeTestClient":
    """Return TestClient for OPTIMADE server, mimicking a remote client"""
    from .utils import client_factory

    return client_factory()(None, False)


@pytest.fixture
def get_good_response(
    client: "OptimadeTestClient", caplog: pytest.LogCaptureFixture
) -> "Callable[[str, bool], Union[Response, Dict[str, Any]]]":
    """Get OPTIMADE response with some sanity checks"""
    import re

    def inner(request: str, raw: bool = False) -> "Union[Response, Dict[str, Any]]":
        if TYPE_CHECKING:
            response: "Union[Response, Dict[str, Any]]"

        try:
            response = client.get(request)

            # Ensure the DB was NOT touched
            assert (
                re.match(
                    r".*Updating Node [0-9]+ in DB!.*", caplog.text, flags=re.DOTALL
                )
                is None
            ), caplog.text

            assert response.status_code == 200, f"Request failed: {response.json()}"

            if not raw:
                response = response.json()

        except Exception:
            print("Request attempted:")
            print(f"{client.base_url}{client.version}{request}")
            raise
        else:
            return response

    return inner


@pytest.fixture
def check_keys() -> "Callable[[List[str], Iterable], None]":
    """Utility function to help validate dict keys"""

    def inner(
        keys: "List[str]",
        response_subset: "Iterable",
    ) -> None:
        for key in keys:
            assert (
                key in response_subset
            ), f"{key} missing from response {response_subset}"

    return inner


@pytest.fixture
def check_response(
    get_good_response: "Callable[[str, bool], Union[Response, Dict[str, Any]]]",
) -> "Callable[[str, List[str], int, bool, bool], None]":
    """Fixture to check response using client fixture"""
    from optimade.server.config import CONFIG

    def inner(
        request: str,
        expected_uuid: "List[str]",
        page_limit: int = CONFIG.page_limit,
        expect_id: bool = False,
        expected_as_is: bool = False,
    ) -> None:
        # Sort by immutable_id
        if "sort=" not in request:
            request += "&sort=immutable_id"

        response = get_good_response(request, False)
        assert isinstance(response, dict)

        if expect_id:
            response_uuids = [struct["id"] for struct in response["data"]]
        else:
            # Expect UUIDs (immutable_id)
            response_uuids = [
                struct["attributes"]["immutable_id"] for struct in response["data"]
            ]
        assert response["meta"]["data_returned"] == len(expected_uuid)

        if not expected_as_is:
            expected_uuid = sorted(expected_uuid)

        if len(expected_uuid) > page_limit:
            assert expected_uuid[:page_limit] == response_uuids
        else:
            assert expected_uuid == response_uuids

    return inner


@pytest.fixture
def check_error_response(
    remote_client: "OptimadeTestClient", caplog: pytest.LogCaptureFixture
) -> "Callable[[str, Optional[int], Optional[str], Optional[str]], None]":
    """General method for testing expected erroneous response"""
    import re

    def inner(
        request: str,
        expected_status: "Optional[int]" = None,
        expected_title: "Optional[str]" = None,
        expected_detail: "Optional[str]" = None,
    ) -> None:
        response: "Optional[Response]" = None
        try:
            response = remote_client.get(request)

            # Ensure the DB was NOT touched
            assert (
                re.match(
                    r".*Updating Node [0-9]+ in AiiDA DB!.*",
                    caplog.text,
                    flags=re.DOTALL,
                )
                is None
            ), caplog.text
            assert (
                re.match(
                    r".*Upserting Node [0-9]+ in MongoDB!.*",
                    caplog.text,
                    flags=re.DOTALL,
                )
                is None
            ), caplog.text

            assert response is not None

            assert response.status_code == expected_status, (
                "Request should have been an error with status code "
                f"{expected_status}, but instead {response.status_code} was received."
                f"\nResponse:\n{response.json()}",
            )

            json_response: "Dict[str, Any]" = response.json()
            assert len(json_response["errors"]) == 1, json_response.get(
                "errors", "'errors' not found"
            )
            assert json_response["meta"]["data_returned"] == 0, json_response.get(
                "meta", "'meta' not found"
            )

            error = json_response["errors"][0]
            assert str(expected_status) == error["status"], error
            assert expected_title == error["title"], error

            if expected_detail is None:
                expected_detail = "Error trying to process rule "
                assert error["detail"].startswith(expected_detail), error
            else:
                assert expected_detail == error["detail"], error

        except Exception:
            print("Request attempted:")
            print(f"{remote_client.base_url}{remote_client.version}{request}")
            if response:
                print(f"\nCaptured response:\n{response}")
            raise

    return inner
