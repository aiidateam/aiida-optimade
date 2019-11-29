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
os.environ["AIIDA_PROFILE"] = "optimade_v1_aiida_sqla"

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


class TestSingleStructureEndpointTests(BaseTestCases.EndpointTests):

    test_id = "1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        assert "data" in self.json_response
        assert self.json_response["data"]["id"] == self.test_id
        assert self.json_response["data"]["type"] == "structures"
        assert "attributes" in self.json_response["data"]
        assert (
            f"{CONFIG.provider['prefix']}{CONFIG.provider_fields['structures'][0]}"
            in self.json_response["data"]["attributes"]
        )


class TestSingleStructureEndpointEmptyTest(BaseTestCases.EndpointTests):

    test_id = "0"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        assert "data" in self.json_response
        assert self.json_response["data"] is None


class TestFilterTests(unittest.TestCase):

    client = CLIENT

    @pytest.mark.skip(
        "Un-skip when a fix for optimade-python-tools issue #102 is in place."
    )
    def test_custom_field(self):
        request = f'/structures?filter={CONFIG.provider["prefix"]}{CONFIG.provider_fields["structures"][0]}="2019-11-19T18:42:25.844780+01:00"'
        expected_ids = ["1"]
        self._check_response(request, expected_ids)

    def test_id(self):
        request = "/structures?filter=id=7"
        expected_ids = ["7"]
        self._check_response(request, expected_ids)

    def test_geq(self):
        request = "/structures?filter=nelements>=18"
        expected_ids = ["1048"]
        self._check_response(request, expected_ids)

    def test_gt(self):
        request = "/structures?filter=nelements>17"
        expected_ids = ["1048"]
        self._check_response(request, expected_ids)

    def test_gt_none(self):
        request = "/structures?filter=nelements>18"
        expected_ids = []
        self._check_response(request, expected_ids)

    def test_list_has(self):
        request = '/structures?filter=elements HAS "Ga"'
        expected_ids = ["574", "658"]
        self._check_response(request, expected_ids)

    def test_page_limit(self):
        request = '/structures?filter=elements HAS "Ge"&page_limit=2'
        expected_ids = ["161", "247", "324", "367", "705"]
        self._check_response(request, expected_ids, page_limit=2)

        request = '/structures?page_limit=2&filter=elements HAS "Ge"'
        self._check_response(request, expected_ids, page_limit=2)

    def test_list_has_all(self):
        request = '/structures?filter=elements HAS ALL "Ge","Na","Al","Cl","O"'
        expected_ids = ["161"]
        self._check_response(request, expected_ids)

    def test_list_has_any(self):
        elements = '"La","Ba"'
        request = f"/structures?filter=elements HAS ALL {elements}"
        expected_ids = ["52"]
        self._check_response(request, expected_ids)

        request = f"/structures?filter=elements HAS ANY {elements}"
        expected_ids = [
            "48",
            "52",
            "60",
            "65",
            "66",
            "67",
            "386",
            "429",
            "475",
            "537",
            "602",
            "603",
            "705",
            "727",
            "1045",
            "1047",
            "1048",
            "1050",
            "1054",
            "1087",
        ]
        self._check_response(request, expected_ids)

    def test_list_length_basic(self):
        request = "/structures?filter=LENGTH elements = 18"
        expected_ids = ["1048"]
        self._check_response(request, expected_ids)

    def test_list_length(self):
        request = "/structures?filter=LENGTH elements = 17"
        expected_ids = ["1047"]
        self._check_response(request, expected_ids)

        request = "/structures?filter=LENGTH elements >= 17"
        expected_ids = ["1047", "1048"]
        self._check_response(request, expected_ids)

        request = "/structures?filter=LENGTH cartesian_site_positions > 5000"
        expected_ids = ["302", "683"]
        self._check_response(request, expected_ids)

    @pytest.mark.skip("HAS ONLY is not implemented.")
    def test_list_has_only(self):
        request = '/structures?filter=elements HAS ONLY "Ac"'
        expected_ids = [""]
        self._check_response(request, expected_ids)

    @pytest.mark.skip("Zips are not implemented.")
    def test_list_correlated(self):
        request = '/structures?filter=elements:elements_ratios HAS "Ag":"0.2"'
        expected_ids = [""]
        self._check_response(request, expected_ids)

    def test_saved_extras_is_known(self):
        request = "/structures?filter=nsites IS KNOWN AND nsites>=5280"
        expected_ids = ["302", "683"]
        self._check_response(request, expected_ids)

        request = "/structures?filter=lattice_vectors IS KNOWN AND nsites>=5280"
        expected_ids = ["302", "683"]
        self._check_response(request, expected_ids)

    def test_node_columns_is_known(self):
        request = f"/structures?filter={CONFIG.provider['prefix']}{CONFIG.provider_fields['structures'][0]} IS KNOWN AND nsites>=5280"
        expected_ids = ["302", "683"]
        self._check_response(request, expected_ids)

        request = "/structures?filter=last_modified IS KNOWN AND nsites>=5280"
        expected_ids = ["302", "683"]
        self._check_response(request, expected_ids)

        request = "/structures?filter=id IS KNOWN AND nsites>=5280"
        expected_ids = ["302", "683"]
        self._check_response(request, expected_ids)

    def test_node_column_fields(self):
        request = '/structures?filter=id="302"'
        expected_ids = ["302"]
        self._check_response(request, expected_ids)

    def test_saved_extras_fields(self):
        request = '/structures?filter=chemical_formula_anonymous CONTAINS "A2B3"'
        expected_ids = ["1038", "1045"]
        self._check_response(request, expected_ids)

    def test_string_contains(self):
        request = '/structures?filter=chemical_formula_descriptive CONTAINS "Ag4Cl"'
        expected_ids = ["285", "550"]
        self._check_response(request, expected_ids)

    def test_string_start(self):
        request = '/structures?filter=chemical_formula_descriptive STARTS WITH "H"'
        expected_ids = ["68", "119", "977"]
        self._check_response(request, expected_ids)

    def test_string_end(self):
        request = '/structures?filter=chemical_formula_descriptive ENDS WITH "0}9"'
        expected_ids = ["63", "64", "1080"]
        self._check_response(request, expected_ids)

    def test_list_has_and(self):
        request = '/structures?filter=elements HAS "Na" AND nelements=18'
        expected_ids = ["1048"]
        self._check_response(request, expected_ids)

    def test_not_or_and_precedence(self):
        request = '/structures?filter=NOT elements HAS "Na" AND nelements=5'
        expected_ids = ["327", "445", "473", "666"]
        self._check_response(request, expected_ids)

        request = '/structures?filter=nelements=5 AND NOT elements HAS "Na"'
        expected_ids = ["327", "445", "473", "666"]
        self._check_response(request, expected_ids)

        request = (
            '/structures?filter=NOT elements HAS "Na" AND nelements=5 OR nsites>5000'
        )
        expected_ids = ["302", "327", "445", "473", "666", "683"]
        self._check_response(request, expected_ids)

        request = '/structures?filter=elements HAS "Na" AND nelements>1 AND nsites>5000'
        expected_ids = ["302", "683"]
        self._check_response(request, expected_ids)

    def test_brackets(self):
        request = '/structures?filter=elements HAS "Ga" AND nelements=7 OR nsites=464'
        expected_ids = ["382", "574", "658", "1055"]
        self._check_response(request, expected_ids)

        request = '/structures?filter=(elements HAS "Ga" AND nelements=7) OR (elements HAS "Ga" AND nsites=464)'
        expected_ids = ["574", "658"]
        self._check_response(request, expected_ids)

    def _check_response(self, request, expected_id, page_limit=None):
        if not page_limit:
            page_limit = CONFIG.page_limit
        try:
            response = self.client.get(request)
            assert response.status_code == 200, f"Request failed: {response.json()}"

            response = response.json()
            response_ids = [struct["id"] for struct in response["data"]]
            assert response["meta"]["data_returned"] == len(expected_id)
            if len(expected_id) > page_limit:
                assert expected_id[:page_limit] == response_ids
            else:
                assert expected_id == response_ids
        except Exception as exc:
            print("Request attempted:")
            print(f"{self.client.base_url}{request}")
            raise exc
