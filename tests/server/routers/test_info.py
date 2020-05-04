import pytest

from optimade.models import (
    InfoResponse,
    EntryInfoResponse,
    BaseInfoAttributes,
    EntryInfoResource,
)

from ..utils import EndpointTests


class TestInfoEndpoint(EndpointTests):
    """Tests for /info"""

    request_str = "/info"
    response_cls = InfoResponse

    def test_info_endpoint_attributes(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert self.json_response["data"]["type"] == "info"
        assert self.json_response["data"]["id"] == "/"
        assert "attributes" in self.json_response["data"]
        attributes = list(BaseInfoAttributes.schema()["properties"].keys())
        self.check_keys(attributes, self.json_response["data"]["attributes"])


class TestInfoStructuresEndpoint(EndpointTests):
    """Tests for /info/structures"""

    request_str = "/info/structures"
    response_cls = EntryInfoResponse

    def test_info_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        data = EntryInfoResource.schema()["required"]
        self.check_keys(data, self.json_response["data"])


@pytest.mark.skip("References has not yet been implemented")
class TestInfoReferencesEndpoint(EndpointTests):
    """Tests for /info/references"""

    request_str = "/info/references"
    response_cls = EntryInfoResponse

    def test_info_references_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        data = EntryInfoResource.schema()["required"]
        self.check_keys(data, self.json_response["data"])
