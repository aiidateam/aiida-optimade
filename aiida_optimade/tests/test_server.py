# pylint: disable=no-member,wrong-import-position
import os

import unittest
import pytest

from starlette.testclient import TestClient

from aiida_optimade.config import CONFIG
from optimade.validator import ImplementationValidator

# this must be changed before app is imported
# some tests currently depend on this value remaining at 5
CONFIG.page_limit = 5  # noqa: E402

# Use specific AiiDA profile
os.environ["AIIDA_PROFILE"] = "optimade_sqla"

from optimade.models import (
    ResponseMeta,
    ReferenceResponseMany,
    ReferenceResponseOne,
    StructureResponseMany,
    StructureResponseOne,
    EntryInfoResponse,
    InfoResponse,
    BaseInfoAttributes,
    EntryInfoResource,
)

from aiida_optimade.main import app
from aiida_optimade.routers import structures, info

# need to explicitly set base_url, as the default "http://testserver"
# does not validate as pydantic UrlStr model
app.include_router(structures.router)
app.include_router(info.router)
CLIENT = TestClient(app, base_url="http://localhost:5000/optimade")


@pytest.mark.skip("References has not yet been implemented.")
class TestServerTestWithValidator(unittest.TestCase):
    def test_with_validator(self):
        validator = ImplementationValidator(client=CLIENT, verbosity=2)
        validator.main()
        assert validator.valid is True


class BaseTestCases:
    class EndpointTests(unittest.TestCase):
        """ Base test class for common tests of endpoints. """

        request_str = None
        response_cls = None

        @classmethod
        def setUpClass(cls):
            cls.client = CLIENT
            cls.response = cls.client.get(cls.request_str)
            cls.json_response = cls.response.json()

        def check_keys(self, keys, response_subset):
            for key in keys:
                assert (
                    key in response_subset
                ), f"{key} missing from response {response_subset}"

        def test_response_okay(self):
            assert (
                self.response.status_code == 200
            ), f"Request to {self.request_str} failed: {self.json_response}"

        def test_meta_response(self):
            assert "meta" in self.json_response
            meta_required_keys = ResponseMeta.schema().get("required")
            self.check_keys(meta_required_keys, self.json_response["meta"])

        def test_serialize_response(self):
            assert (
                self.response_cls is not None
            ), "Response model class unset for this endpoint"
            self.response_cls(**self.json_response)  # pylint: disable=not-callable


class TestInfoEndpointTests(BaseTestCases.EndpointTests):

    request_str = "/info"
    response_cls = InfoResponse

    def test_info_endpoint_attributes(self):
        assert "data" in self.json_response
        assert self.json_response["data"]["type"] == "info"
        assert self.json_response["data"]["id"] == "/"
        assert "attributes" in self.json_response["data"]
        attributes = list(BaseInfoAttributes.schema().get("properties").keys())
        self.check_keys(attributes, self.json_response["data"]["attributes"])


@pytest.mark.skip("References has not yet been implemented.")
class TestInfoReferencesEndpointTests(BaseTestCases.EndpointTests):

    request_str = "/info/references"
    response_cls = EntryInfoResponse

    def test_info_references_endpoint_data(self):
        assert "data" in self.json_response
        data = EntryInfoResource.schema().get("required")
        self.check_keys(data, self.json_response["data"])


class TestInfoStructuresEndpointTests(BaseTestCases.EndpointTests):

    request_str = "/info/structures"
    response_cls = EntryInfoResponse

    def test_info_structures_endpoint_data(self):
        assert "data" in self.json_response
        data = EntryInfoResource.schema().get("required")
        self.check_keys(data, self.json_response["data"])


@pytest.mark.skip("References has not yet been implemented.")
class TestReferencesEndpointTests(BaseTestCases.EndpointTests):

    request_str = "/references"
    response_cls = ReferenceResponseMany


@pytest.mark.skip("References has not yet been implemented.")
class TestSingleReferenceEndpointTests(BaseTestCases.EndpointTests):

    test_id = "Dijkstra1968"
    request_str = f"/references/{test_id}"
    response_cls = ReferenceResponseOne


class TestStructuresEndpointTests(BaseTestCases.EndpointTests):

    request_str = "/structures"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        assert "data" in self.json_response
        assert len(self.json_response["data"]) == CONFIG.page_limit
        assert "meta" in self.json_response
        assert self.json_response["meta"]["data_available"] == 1089
        assert self.json_response["meta"]["more_data_available"]

    def test_get_next_responses(self):
        cursor = self.json_response["data"].copy()
        more_data_available = True
        next_request = self.json_response["links"]["next"]

        id_ = len(cursor)
        while more_data_available and id_ < CONFIG.page_limit * 5:
            next_response = self.client.get(next_request).json()
            next_request = next_response["links"]["next"]
            cursor.extend(next_response["data"])
            more_data_available = next_response["meta"]["more_data_available"]
            if more_data_available:
                assert len(next_response["data"]) == CONFIG.page_limit
            else:
                assert len(next_response["data"]) == 1089 % CONFIG.page_limit
            id_ += len(next_response["data"])

        assert len(cursor) == id_


@pytest.mark.skip("Must be updated with local test data.")
class TestSingleStructureEndpointTests(BaseTestCases.EndpointTests):

    test_id = "mpf_1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        assert "data" in self.json_response
        assert self.json_response["data"]["id"] == self.test_id
        assert self.json_response["data"]["type"] == "structures"
        assert "attributes" in self.json_response["data"]
        assert "_exmpl__mp_chemsys" in self.json_response["data"]["attributes"]


class TestSingleStructureEndpointEmptyTest(BaseTestCases.EndpointTests):

    test_id = "0"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        assert "data" in self.json_response
        assert self.json_response["data"] is None


@pytest.mark.skip("Must be updated with local test data.")
class TestFilterTests(unittest.TestCase):

    client = CLIENT

    def test_custom_field(self):
        request = '/structures?filter=_exmpl__mp_chemsys="Ac"'
        expected_ids = ["mpf_1"]
        self._check_response(request, expected_ids)

    def test_id(self):
        request = "/structures?filter=id=mpf_2"
        expected_ids = ["mpf_2"]
        self._check_response(request, expected_ids)

    def test_geq(self):
        request = "/structures?filter=nelements>=9"
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids)

    def test_gt(self):
        request = "/structures?filter=nelements>8"
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids)

    def test_gt_none(self):
        request = "/structures?filter=nelements>9"
        expected_ids = []
        self._check_response(request, expected_ids)

    def test_list_has(self):
        request = '/structures?filter=elements HAS "Ti"'
        expected_ids = ["mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids)

    def test_page_limit(self):
        request = '/structures?filter=elements HAS "Ac"&page_limit=2'
        expected_ids = ["mpf_1", "mpf_2"]
        self._check_response(request, expected_ids)

        request = '/structures?page_limit=2&filter=elements HAS "Ac"'
        expected_ids = ["mpf_1", "mpf_2"]
        self._check_response(request, expected_ids)

    def test_list_has_all(self):
        request = '/structures?filter=elements HAS ALL "Ba","F","H","Mn","O","Re","Si"'
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids)

        request = '/structures?filter=elements HAS ALL "Re","Ti"'
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids)

    def test_list_has_any(self):
        request = '/structures?filter=elements HAS ANY "Re","Ti"'
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids)

    def test_list_length_basic(self):
        request = "/structures?filter=LENGTH elements = 9"
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids)

    def test_list_length(self):
        request = "/structures?filter=LENGTH elements = 9"
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids)

        request = "/structures?filter=LENGTH elements >= 9"
        expected_ids = ["mpf_3819"]
        self._check_response(request, expected_ids)

        request = "/structures?filter=LENGTH structure_features > 0"
        expected_ids = []
        self._check_response(request, expected_ids)

    def test_list_has_only(self):
        request = '/structures?filter=elements HAS ONLY "Ac"'
        expected_ids = ["mpf_1"]
        self._check_response(request, expected_ids)

    def test_list_correlated(self):
        request = '/structures?filter=elements:elements_ratios HAS "Ag":"0.2"'
        expected_ids = ["mpf_259"]
        self._check_response(request, expected_ids)

    def test_is_known(self):
        request = "/structures?filter=nsites IS KNOWN AND nsites>=44"
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids)

        request = "/structures?filter=lattice_vectors IS KNOWN AND nsites>=44"
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids)

    def test_aliased_is_known(self):
        request = "/structures?filter=id IS KNOWN AND nsites>=44"
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids)

        request = "/structures?filter=chemical_formula_reduced IS KNOWN AND nsites>=44"
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids)

        request = (
            "/structures?filter=chemical_formula_descriptive IS KNOWN AND nsites>=44"
        )
        expected_ids = ["mpf_551", "mpf_3803", "mpf_3819"]
        self._check_response(request, expected_ids)

    def test_aliased_fields(self):
        request = '/structures?filter=chemical_formula_anonymous="A"'
        expected_ids = ["mpf_1", "mpf_200"]
        self._check_response(request, expected_ids)

        request = '/structures?filter=chemical_formula_anonymous CONTAINS "A2BC"'
        expected_ids = ["mpf_2", "mpf_3", "mpf_110"]
        self._check_response(request, expected_ids)

    def test_string_contains(self):
        request = '/structures?filter=chemical_formula_descriptive CONTAINS "c2Ag"'
        expected_ids = ["mpf_3", "mpf_2"]
        self._check_response(request, expected_ids)

    def test_string_start(self):
        request = (
            '/structures?filter=chemical_formula_descriptive STARTS WITH "Ag2CSNCl"'
        )
        expected_ids = ["mpf_259"]
        self._check_response(request, expected_ids)

    def test_string_end(self):
        request = '/structures?filter=chemical_formula_descriptive ENDS WITH "NClO4"'
        expected_ids = ["mpf_259"]
        self._check_response(request, expected_ids)

    def test_list_has_and(self):
        request = '/structures?filter=elements HAS "Ac" AND nelements=1'
        expected_ids = ["mpf_1"]
        self._check_response(request, expected_ids)

    def test_not_or_and_precedence(self):
        request = '/structures?filter=NOT elements HAS "Ac" AND nelements=1'
        expected_ids = ["mpf_200"]
        self._check_response(request, expected_ids)

        request = '/structures?filter=nelements=1 AND NOT elements HAS "Ac"'
        expected_ids = ["mpf_200"]
        self._check_response(request, expected_ids)

        request = '/structures?filter=NOT elements HAS "Ac" AND nelements=1 OR nsites=1'
        expected_ids = ["mpf_1", "mpf_200"]
        self._check_response(request, expected_ids)

        request = '/structures?filter=elements HAS "Ac" AND nelements>1 AND nsites=1'
        expected_ids = []
        self._check_response(request, expected_ids)

    def test_brackets(self):
        request = '/structures?filter=elements HAS "Ac" AND nelements=1 OR nsites=1'
        expected_ids = ["mpf_200", "mpf_1"]
        self._check_response(request, expected_ids)

        request = '/structures?filter=(elements HAS "Ac" AND nelements=1) OR (elements HAS "Ac" AND nsites=1)'
        expected_ids = ["mpf_1"]
        self._check_response(request, expected_ids)

    def _check_response(self, request, expected_id):
        try:
            response = self.client.get(request)
            assert response.status_code == 200, f"Request failed: {response.json()}"

            response = response.json()
            response_ids = [struct["id"] for struct in response["data"]]
            assert sorted(expected_id) == sorted(response_ids)
            assert response["meta"]["data_returned"] == len(expected_id)
        except Exception as exc:
            print("Request attempted:")
            print(f"{self.client.base_url}{request}")
            raise exc
