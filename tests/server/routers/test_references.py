from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ..utils import EndpointTests

if TYPE_CHECKING:
    from optimade.models import ReferenceResponseMany, ReferenceResponseOne

pytestmark = pytest.mark.skip("References has not yet been implemented")


def _get_optimade_reference_response_model(
    name: str,
) -> type[ReferenceResponseMany] | type[ReferenceResponseOne]:
    from optimade.models import ReferenceResponseMany, ReferenceResponseOne

    if name == "ReferenceResponseMany":
        return ReferenceResponseMany
    if name == "ReferenceResponseOne":
        return ReferenceResponseOne
    raise ValueError(f"Unknown response model name: {name}")


class TestReferencesEndpoint(EndpointTests):
    """Tests for /references"""

    request_str = "/references"
    response_cls = _get_optimade_reference_response_model("ReferenceResponseMany")


class TestSingleReferenceEndpoint(EndpointTests):
    """Tests for /references/<entry_id>"""

    test_id = "dijkstra1968"
    request_str = f"/references/{test_id}"
    response_cls = _get_optimade_reference_response_model("ReferenceResponseOne")


class TestSingleReferenceEndpointDifficult(EndpointTests):
    """Tests for /references/<entry_id>,
    where <entry_id> contains difficult characters"""

    test_id = "dummy/20.19"
    request_str = f"/references/{test_id}"
    response_cls = _get_optimade_reference_response_model("ReferenceResponseOne")


class TestMissingSingleReferenceEndpoint(EndpointTests):
    """Tests for /references/<entry_id> for unknown <entry_id>"""

    test_id = "random_string_that_is_not_in_test_data"
    request_str = f"/references/{test_id}"
    response_cls = _get_optimade_reference_response_model("ReferenceResponseOne")

    def test_references_endpoint_data(self) -> None:
        """Check known properties/attributes for successful response"""
        assert isinstance(self.json_response, dict)
        assert "data" in self.json_response
        assert "meta" in self.json_response
        assert self.json_response["data"] is None
        assert self.json_response["meta"]["data_returned"] == 0
        assert not self.json_response["meta"]["more_data_available"]
