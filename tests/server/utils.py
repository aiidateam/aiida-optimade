# pylint: disable=no-name-in-module,too-many-arguments
import json
from typing import Iterable

from pydantic import BaseModel
import pytest

from optimade.models import ResponseMeta


class EndpointTests:
    """Base class for common tests of endpoints"""

    request_str: str = None
    response_cls: BaseModel = None

    response = None
    json_response = None

    @pytest.fixture(autouse=True)
    def get_response(self, client):
        """Get response from client"""
        self.response = client.get(self.request_str)
        self.json_response = self.response.json()
        yield
        self.response = None
        self.json_response = None

    @staticmethod
    def check_keys(keys: list, response_subset: Iterable):
        """Utility function to help validate dict keys"""
        for key in keys:
            assert (
                key in response_subset
            ), f"{key} missing from response {response_subset}"

    def test_response_okay(self):
        """Make sure the response was successful"""
        assert self.response.status_code == 200, (
            f"Request to {self.request_str} failed: "
            f"{json.dumps(self.json_response, indent=2)}"
        )

    def test_meta_response(self):
        """General test for `meta` property in response"""
        assert "meta" in self.json_response
        meta_required_keys = ResponseMeta.schema()["required"]
        meta_optional_keys = list(
            set(ResponseMeta.schema()["properties"].keys()) - set(meta_required_keys)
        )
        implemented_optional_keys = ["data_available", "implementation"]

        self.check_keys(meta_required_keys, self.json_response["meta"])
        self.check_keys(implemented_optional_keys, meta_optional_keys)
        self.check_keys(implemented_optional_keys, self.json_response["meta"])

    def test_serialize_response(self):
        """General test for response JSON and pydantic model serializability"""
        assert self.response_cls is not None, "Response class unset for this endpoint"
        self.response_cls(**self.json_response)  # pylint: disable=not-callable
