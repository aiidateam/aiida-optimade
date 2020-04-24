# pylint: disable=import-outside-toplevel,no-name-in-module
import abc

from pydantic import BaseModel

from fastapi.testclient import TestClient


def get_client() -> TestClient:
    """Return TestClient for OPTIMADE server"""
    from aiida_optimade.main import APP
    from aiida_optimade.routers import info, structures

    # We need to remove the version prefixes in order to have the tests run correctly.
    APP.include_router(info.ROUTER)
    APP.include_router(structures.ROUTER)
    # need to explicitly set base_url, as the default "http://testserver"
    # does not validate as pydantic AnyUrl model
    return TestClient(APP, base_url="http://example.org/v0")


class SetClient(abc.ABC):
    """Metaclass to instantiate the TestClients once"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = None

    @property
    def client(self) -> TestClient:
        """Return test client for OPTIMADE server"""
        if self._client is None:
            self._client = get_client()
        return self._client

    # pylint: disable=no-member
    def check_error_response(
        self,
        request: str,
        expected_status: int = None,
        expected_title: str = None,
        expected_detail: str = None,
    ):
        """General method for testing expected errornous response"""
        try:
            response = self.client.get(request)
            self.assertEqual(
                response.status_code,
                expected_status,
                msg="Request should have been an error with status code "
                f"{expected_status}, but instead {response.status_code} was received."
                f"\nResponse:\n{response.json()}",
            )
            response = response.json()
            self.assertEqual(len(response["errors"]), 1)
            self.assertEqual(response["meta"]["data_returned"], 0)

            error = response["errors"][0]
            self.assertEqual(str(expected_status), error["status"])
            self.assertEqual(expected_title, error["title"])

            if expected_detail is None:
                expected_detail = "Error trying to process rule "
                self.assertTrue(error["detail"].startswith(expected_detail))
            else:
                self.assertEqual(expected_detail, error["detail"])

        except Exception as exc:
            print("Request attempted:")
            print(f"{self.client.base_url}{request}")
            raise exc


class EndpointTestsMixin(SetClient):
    """Mixin "base" class for common tests between endpoints"""

    request_str: str = None
    response_cls: BaseModel = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.response = self.client.get(self.request_str)
        self.json_response = self.response.json()
        self.assertEqual(
            self.response.status_code,
            200,
            msg=f"Request failed: {self.response.json()}",
        )

    def test_meta_response(self):
        """General test for `meta` property in response"""
        self.assertTrue("meta" in self.json_response)
        meta_required_keys = [
            "query",
            "api_version",
            "time_stamp",
            "data_returned",
            "more_data_available",
            "provider",
        ]
        meta_optional_keys = ["data_available", "implementation"]

        self.check_keys(meta_required_keys, self.json_response["meta"])
        self.check_keys(meta_optional_keys, self.json_response["meta"])

    def test_serialize_response(self):
        """General test for response JSON and pydantic model serializability"""
        self.assertTrue(
            self.response_cls is not None, msg="Response class unset for this endpoint"
        )
        self.response_cls(**self.json_response)  # pylint: disable=not-callable

    def check_keys(self, keys: list, response_subset: dict):
        """Utility function to help validate dict keys"""
        for key in keys:
            self.assertTrue(
                key in response_subset,
                msg="{} missing from response {}".format(key, response_subset),
            )
