import unittest

from optimade.models import (
    StructureResponseMany,
    StructureResponseOne,
    ReferenceResource,
)

from ..utils import EndpointTestsMixin


class StructuresEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /structures"""

    request_str = "/structures"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response

        # Should match page_limit in test_config.json
        assert len(self.json_response["data"]) == 15

        assert "meta" in self.json_response
        assert self.json_response["meta"]["data_available"] == 1089
        assert self.json_response["meta"]["more_data_available"]

    def test_get_next_responses(self):
        """Check pagination"""
        total_data = self.json_response["meta"]["data_available"]
        page_limit = 5

        response = self.client.get(self.request_str + f"?page_limit={page_limit}")
        json_response = response.json()
        assert response.status_code == 200, f"Request failed: {response.json()}"

        cursor = json_response["data"].copy()
        assert json_response["meta"]["more_data_available"]
        more_data_available = True
        next_request = json_response["links"]["next"]

        id_ = len(cursor)
        while more_data_available and id_ < page_limit * 3:
            next_response = self.client.get(next_request).json()
            next_request = next_response["links"]["next"]
            cursor.extend(next_response["data"])
            more_data_available = next_response["meta"]["more_data_available"]
            if more_data_available:
                assert len(next_response["data"]) == page_limit
            else:
                assert len(next_response["data"]) == total_data % page_limit
            id_ += len(next_response["data"])

        assert len(cursor) == id_


class SingleStructureEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /structures/<entry_id>"""

    test_id = "mpf_1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        self.assertTrue("data" in self.json_response)
        self.assertEqual(self.json_response["data"]["id"], self.test_id)
        self.assertEqual(self.json_response["data"]["type"], "structures")
        self.assertTrue("attributes" in self.json_response["data"])
        self.assertTrue("_exmpl_chemsys" in self.json_response["data"]["attributes"])


class MissingSingleStructureEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /structures/<entry_id> for unknown <entry_id>"""

    test_id = "mpf_random_string_that_is_not_in_test_data"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        self.assertTrue("data" in self.json_response)
        self.assertTrue("meta" in self.json_response)
        self.assertEqual(self.json_response["data"], None)
        self.assertEqual(self.json_response["meta"]["data_returned"], 0)
        self.assertEqual(self.json_response["meta"]["more_data_available"], False)


class SingleStructureWithRelationshipsTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /structures/<entry_id>, where <entry_id> has relationships"""

    test_id = "mpf_1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        self.assertTrue("data" in self.json_response)
        self.assertEqual(self.json_response["data"]["id"], self.test_id)
        self.assertEqual(self.json_response["data"]["type"], "structures")
        self.assertTrue("attributes" in self.json_response["data"])
        self.assertTrue("relationships" in self.json_response["data"])
        self.assertDictEqual(
            self.json_response["data"]["relationships"],
            {"references": {"data": [{"type": "references", "id": "dijkstra1968"}]}},
        )
        self.assertTrue("included" in self.json_response)
        self.assertEqual(
            len(self.json_response["data"]["relationships"]["references"]["data"]),
            len(self.json_response["included"]),
        )

        ReferenceResource(**self.json_response["included"][0])


class MultiStructureWithSharedRelationshipsTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /structures for entries with shared relationships"""

    request_str = "/structures?filter=id=mpf_1 OR id=mpf_2"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        # mpf_1 and mpf_2 both contain the same reference relationship,
        # so the response should not duplicate it
        self.assertTrue("data" in self.json_response)
        self.assertEqual(len(self.json_response["data"]), 2)
        self.assertTrue("included" in self.json_response)
        self.assertEqual(len(self.json_response["included"]), 1)


class MultiStructureWithRelationshipsTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /structures for mixed entries with and without relationships"""

    request_str = "/structures?filter=id=mpf_1 OR id=mpf_23"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        # mpf_23 contains no relationships, which shouldn't break anything
        self.assertTrue("data" in self.json_response)
        self.assertEqual(len(self.json_response["data"]), 2)
        self.assertTrue("included" in self.json_response)
        self.assertEqual(len(self.json_response["included"]), 1)


class MultiStructureWithOverlappingRelationshipsTests(
    EndpointTestsMixin, unittest.TestCase
):
    """Tests for /structures with entries with overlapping relationships

    One entry has multiple relationships, another entry has other relationships,
    some of these relationships overlap between the entries, others don't.
    """

    request_str = "/structures?filter=id=mpf_1 OR id=mpf_3"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        self.assertTrue("data" in self.json_response)
        self.assertEqual(len(self.json_response["data"]), 2)
        self.assertTrue("included" in self.json_response)
        self.assertEqual(len(self.json_response["included"]), 2)
