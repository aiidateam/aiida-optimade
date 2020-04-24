# pylint: disable=relative-beyond-top-level
import unittest

from optimade.models import InfoResponse, EntryInfoResponse

from ..utils import EndpointTestsMixin


class InfoEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /info"""

    request_str = "/info"
    response_cls = InfoResponse

    def test_info_endpoint_attributes(self):
        """Check known properties/attributes for successful response"""
        self.assertTrue("data" in self.json_response)
        self.assertEqual(self.json_response["data"]["type"], "info")
        self.assertEqual(self.json_response["data"]["id"], "/")
        self.assertTrue("attributes" in self.json_response["data"])
        attributes = [
            "api_version",
            "available_api_versions",
            "formats",
            "entry_types_by_format",
            "available_endpoints",
        ]
        self.check_keys(attributes, self.json_response["data"]["attributes"])


class InfoStructuresEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /info/structures"""

    request_str = "/info/structures"
    response_cls = EntryInfoResponse

    def test_info_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        self.assertTrue("data" in self.json_response)
        data_keys = ["description", "properties", "formats", "output_fields_by_format"]
        self.check_keys(data_keys, self.json_response["data"])


class InfoReferencesEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /info/references"""

    request_str = "/info/references"
    response_cls = EntryInfoResponse
