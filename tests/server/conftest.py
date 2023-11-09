from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any, Protocol

    from httpx import Response
    from optimade.server.config import CONFIG

    from .utils import OptimadeTestClient

    class GetGoodResponse(Protocol):
        def __call__(
            self, request: str, raw: bool = False
        ) -> Response | dict[str, Any]:
            ...

    class CheckKeys(Protocol):
        def __call__(self, keys: list[str], response_subset: Iterable) -> None:
            ...

    class CheckResponse(Protocol):
        def __call__(
            self,
            request: str,
            expected_uuid: list[str],
            page_limit: int = CONFIG.page_limit,
            expect_id: bool = False,
            expected_as_is: bool = False,
        ) -> None:
            ...

    class CheckErrorResponse(Protocol):
        def __call__(
            self,
            request: str,
            expected_status: int | None = None,
            expected_title: str | None = None,
            expected_detail: str | None = None,
        ) -> None:
            ...


@pytest.fixture(scope="module")
def client() -> OptimadeTestClient:
    """Return TestClient for OPTIMADE server"""
    from .utils import client_factory

    return client_factory()()


@pytest.fixture(scope="module")
def remote_client() -> OptimadeTestClient:
    """Return TestClient for OPTIMADE server, mimicking a remote client"""
    from .utils import client_factory

    return client_factory()(raise_server_exceptions=False)


@pytest.fixture
def get_good_response(
    client: OptimadeTestClient, caplog: pytest.LogCaptureFixture
) -> GetGoodResponse:
    """Get OPTIMADE response with some sanity checks"""

    def inner(request: str, raw: bool = False) -> Response | dict[str, Any]:
        if TYPE_CHECKING:
            response: Response | dict[str, Any]

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
def check_keys() -> CheckKeys:
    """Utility function to help validate dict keys"""

    def inner(
        keys: list[str],
        response_subset: Iterable,
    ) -> None:
        for key in keys:
            assert (
                key in response_subset
            ), f"{key} missing from response {response_subset}"

    return inner


@pytest.fixture
def check_response(
    get_good_response: GetGoodResponse,
) -> CheckResponse:
    """Fixture to check response using client fixture"""
    from optimade.server.config import CONFIG

    def inner(
        request: str,
        expected_uuid: list[str],
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
    remote_client: OptimadeTestClient, caplog: pytest.LogCaptureFixture
) -> CheckErrorResponse:
    """General method for testing expected erroneous response"""

    def inner(
        request: str,
        expected_status: int | None = None,
        expected_title: str | None = None,
        expected_detail: str | None = None,
    ) -> None:
        response: Response | None = None
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

            json_response: dict[str, Any] = response.json()
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
