import pytest

from optimade.models import (
    StructureResponseMany,
    StructureResponseOne,
    ReferenceResource,
)
from optimade.server.config import CONFIG

from ..utils import EndpointTests


class TestStructuresEndpoint(EndpointTests):
    """Tests for /structures"""

    request_str = "/structures"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert len(self.json_response["data"]) == CONFIG.page_limit
        assert "meta" in self.json_response
        assert self.json_response["meta"]["data_available"] == 1089
        assert self.json_response["meta"]["more_data_available"]

    def test_get_next_responses(self, client):
        """Check pagination"""
        total_data = self.json_response["meta"]["data_available"]
        page_limit = 5

        response = client.get(self.request_str + f"?page_limit={page_limit}")
        json_response = response.json()
        assert response.status_code == 200, f"Request failed: {response.json()}"

        cursor = json_response["data"].copy()
        assert json_response["meta"]["more_data_available"]
        more_data_available = True
        next_request = json_response["links"]["next"]

        id_ = len(cursor)
        while more_data_available and id_ < page_limit * 3:
            next_response = client.get(next_request).json()
            next_request = next_response["links"]["next"]
            cursor.extend(next_response["data"])
            more_data_available = next_response["meta"]["more_data_available"]
            if more_data_available:
                assert len(next_response["data"]) == page_limit
            else:
                assert len(next_response["data"]) == total_data % page_limit
            id_ += len(next_response["data"])

        assert len(cursor) == id_


@pytest.mark.skip("Move to functions, where fixtures can be used to set variables.")
class TestSingleStructureEndpoint(EndpointTests):
    """Tests for /structures/<entry_id>"""

    test_id = "1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert self.json_response["data"]["id"] == self.test_id
        assert self.json_response["data"]["type"] == "structures"
        assert "attributes" in self.json_response["data"]
        assert (
            f"_{CONFIG.provider.prefix}_{CONFIG.provider_fields['structures'][0]}"
            in self.json_response["data"]["attributes"]
        )


class TestMissingSingleStructureEndpoint(EndpointTests):
    """Tests for /structures/<entry_id> for unknown <entry_id>"""

    test_id = "0"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert "meta" in self.json_response
        assert self.json_response["data"] is None
        assert self.json_response["meta"]["data_returned"] == 0
        assert not self.json_response["meta"]["more_data_available"]


@pytest.mark.skip("Relationships have not yet been implemented")
class TestSingleStructureWithRelationships(EndpointTests):
    """Tests for /structures/<entry_id>, where <entry_id> has relationships"""

    test_id = "1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert self.json_response["data"]["id"] == self.test_id
        assert self.json_response["data"]["type"] == "structures"
        assert "attributes" in self.json_response["data"]
        assert "relationships" in self.json_response["data"]
        assert self.json_response["data"]["relationships"] == {
            "references": {"data": [{"type": "references", "id": "dijkstra1968"}]}
        }
        assert "included" in self.json_response
        assert len(
            self.json_response["data"]["relationships"]["references"]["data"]
        ) == len(self.json_response["included"])

        ReferenceResource(**self.json_response["included"][0])


@pytest.mark.skip("Relationships have not yet been implemented")
class TestMultiStructureWithSharedRelationships(EndpointTests):
    """Tests for /structures for entries with shared relationships"""

    request_str = "/structures?filter=id=mpf_1 OR id=mpf_2"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        # mpf_1 and mpf_2 both contain the same reference relationship,
        # so the response should not duplicate it
        assert "data" in self.json_response
        assert len(self.json_response["data"]) == 2
        assert "included" in self.json_response
        assert len(self.json_response["included"]) == 1


@pytest.mark.skip("Relationships have not yet been implemented")
class TestMultiStructureWithRelationships(EndpointTests):
    """Tests for /structures for mixed entries with and without relationships"""

    request_str = "/structures?filter=id=mpf_1 OR id=mpf_23"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        # mpf_23 contains no relationships, which shouldn't break anything
        assert "data" in self.json_response
        assert len(self.json_response["data"]) == 2
        assert "included" in self.json_response
        assert len(self.json_response["included"]) == 1


@pytest.mark.skip("Relationships have not yet been implemented")
class TestMultiStructureWithOverlappingRelationships(EndpointTests):
    """Tests for /structures with entries with overlapping relationships

    One entry has multiple relationships, another entry has other relationships,
    some of these relationships overlap between the entries, others don't.
    """

    request_str = "/structures?filter=id=mpf_1 OR id=mpf_3"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert len(self.json_response["data"]) == 2
        assert "included" in self.json_response
        assert len(self.json_response["included"]) == 2
