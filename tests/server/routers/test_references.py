import pytest

from optimade.models import ReferenceResponseMany, ReferenceResponseOne

from ..utils import EndpointTests

pytestmark = pytest.mark.skip("References has not yet been implemented")


class TestReferencesEndpoint(EndpointTests):
    """Tests for /references"""

    request_str = "/references"
    response_cls = ReferenceResponseMany


class TestSingleReferenceEndpoint(EndpointTests):
    """Tests for /references/<entry_id>"""

    test_id = "dijkstra1968"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne


class TestSingleReferenceEndpointDifficult(EndpointTests):
    """Tests for /references/<entry_id>,
    where <entry_id> contains difficult characters"""

    test_id = "dummy/20.19"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne


class TestMissingSingleReferenceEndpoint(EndpointTests):
    """Tests for /references/<entry_id> for unknown <entry_id>"""

    test_id = "random_string_that_is_not_in_test_data"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne

    def test_references_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert "meta" in self.json_response
        assert self.json_response["data"] is None
        assert self.json_response["meta"]["data_returned"] == 0
        assert not self.json_response["meta"]["more_data_available"]
