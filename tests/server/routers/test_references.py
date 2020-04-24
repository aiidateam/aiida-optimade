import unittest
import pytest

from optimade.models import ReferenceResponseMany, ReferenceResponseOne

from ..utils import EndpointTestsMixin

pytestmark = pytest.mark.skip("References has not yet been implemented")


class ReferencesEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /references"""

    request_str = "/references"
    response_cls = ReferenceResponseMany


class SingleReferenceEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /references/<entry_id>"""

    test_id = "dijkstra1968"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne


class SingleReferenceEndpointTestsDifficult(EndpointTestsMixin, unittest.TestCase):
    """Tests for /references/<entry_id>,
    where <entry_id> contains difficult characters"""

    test_id = "dummy/20.19"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne


class MissingSingleReferenceEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /references/<entry_id> for unknown <entry_id>"""

    test_id = "random_string_that_is_not_in_test_data"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne

    def test_references_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        self.assertTrue("data" in self.json_response)
        self.assertTrue("meta" in self.json_response)
        self.assertEqual(self.json_response["data"], None)
        self.assertEqual(self.json_response["meta"]["data_returned"], 0)
        self.assertEqual(self.json_response["meta"]["more_data_available"], False)
