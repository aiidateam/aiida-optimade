"""Test the `filters` query parameter."""
# pylint: disable=missing-function-docstring,protected-access,import-error,too-many-statements
import os
import pytest


@pytest.mark.skip(
    "Un-skip when a fix for optimade-python-tools issue #102 is in place."
)
def test_custom_field(check_response):
    from optimade.server.config import CONFIG

    request = (
        f"/structures?filter=_{CONFIG.provider.prefix}_"
        f'{CONFIG.provider_fields["structures"][0]}'
        '="2019-11-19T18:42:25.844780+01:00"'
    )
    expected_uuids = ["1"]
    check_response(request, expected_uuids)


def test_id(check_response, get_valid_id):
    request = f'/structures?filter=id="{get_valid_id}"'
    expected_ids = [str(get_valid_id)]
    check_response(request, expected_ids, expect_id=True)


def test_geq(check_response):
    request = "/structures?filter=nelements>=18"
    expected_uuids = ["b6175807-826a-459f-8a5a-7bff75ff1d36"]
    check_response(request, expected_uuids)


def test_gt(check_response):
    request = "/structures?filter=nelements>17"
    expected_uuids = ["b6175807-826a-459f-8a5a-7bff75ff1d36"]
    check_response(request, expected_uuids)


def test_gt_none(check_response):
    request = "/structures?filter=nelements>18"
    expected_uuids = []
    check_response(request, expected_uuids)


def test_rhs_statements(check_response, get_valid_id):
    request = "/structures?filter=18<nelements"
    expected_uuids = []
    check_response(request, expected_uuids)

    request = f'/structures?filter="{get_valid_id}"=id'
    expected_ids = [str(get_valid_id)]
    check_response(request, expected_ids, expect_id=True)

    request = "/structures?filter=18<=nelements"
    expected_uuids = ["b6175807-826a-459f-8a5a-7bff75ff1d36"]
    check_response(request, expected_uuids)


def test_list_has(check_response):
    request = '/structures?filter=elements HAS "Ga"'
    expected_uuids = [
        "199bf419-0393-4970-8822-f1014e457d3c",
        "205dfe10-a7e3-44bf-abde-6fbad64a857f",
        "2fe2e894-d97a-4c6e-a633-84ef87084d65",
        "6c32a26e-8423-471a-95fd-64b3d78572e8",
        "85a0662f-13ea-4f99-88cf-041a02807f42",
        "92d952f4-7be1-4f46-9583-2f757f05e455",
        "995de9bb-5b4b-4860-97b9-75160631ef71",
        "a20609c5-fa2a-4299-8ebf-e4e97d7cb980",
        "a805a2f6-792d-4718-b7fb-e34ed900ccd8",
        "a96e823c-7344-435c-ac8a-7942da3f0ee1",
        "b0ded7f2-69f8-4262-bcc2-5e402ddf7f7a",
        "e05977df-619c-4cc4-80ba-eafeb13f58c1",
        "e8f3aaec-4755-451a-b9bf-d6c327b31925",
        "f28033c7-4470-4a1b-a4bc-9e16585c053e",
    ]
    check_response(request, expected_uuids)


def test_page_limit(check_response):
    request = '/structures?filter=elements HAS ALL "Ge","S"&page_limit=2'
    expected_uuids = [
        "02548222-8f47-4fb4-afdb-197e2984f818",
        "40891d6a-a7b5-44a2-bdd1-1d089cef5abc",
        "9b7915de-41a1-4192-95d5-977e33874f14",
        "db08d6af-1e60-4395-afd9-9ed9a417e5e7",
    ]
    check_response(request, expected_uuids, page_limit=2)

    request = '/structures?page_limit=2&filter=elements HAS ALL "Ge","S"'
    check_response(request, expected_uuids, page_limit=2)


def test_list_has_all(check_response):
    request = '/structures?filter=elements HAS ALL "Ge","Na","Al","Cl","O"'
    expected_uuids = ["254947de-54c8-4cdb-afc5-1cee237f9f98"]
    check_response(request, expected_uuids)


def test_list_has_any(check_response):
    elements = '"La","Ba"'
    request = f"/structures?filter=elements HAS ALL {elements}"
    expected_uuids = ["c8368624-e49a-46ad-aef7-daaee4ff89e3"]
    check_response(request, expected_uuids)

    request = f"/structures?filter=elements HAS ANY {elements}"
    expected_uuids = [
        "0abfbfc3-1d88-41e9-8cb1-766065884cff",
        "13f44f8d-63de-4105-bbde-a38469582322",
        "16ed2841-2cbf-4a03-a287-ba7a25b9d57c",
        "198945c9-de17-4f74-b91e-b9f0fcb3ec48",
        "240df533-2527-46c6-8f50-f35fd963707e",
        "2d6282a5-635e-4fcd-9ed2-0ec6147e5b58",
        "540cf17b-458f-4ad2-b430-4d05778430a6",
        "9085fbb2-f563-4ef9-af28-1318ee3abefc",
        "a761cf35-0c5e-4367-87a1-75358f1b1896",
        "b7a911fb-6692-4725-929a-d46cf1b8226a",
        "c6ce6f24-6c5a-4318-93bc-aeea0a51d4d0",
        "fdf06c54-5c9f-4aaa-92b1-b21f62a76fa3",
        "bc170570-ee0a-4a03-8b6f-374b0a3da41c",
        "c8368624-e49a-46ad-aef7-daaee4ff89e3",
        "a2aefddb-f9de-46a1-98c7-a19d40ef507c",
        "27dbaf16-d2ef-4158-bdab-bd686a032a3d",
        "36b56345-43a9-47ed-a8d2-1af2326d94b1",
        "2baf3b77-7631-4206-bc70-dc3f83c3ae57",
        "3763b506-d8ba-43f0-9536-adda02f9b596",
        "3690e480-55f9-4371-a2fb-f8679039d13a",
        "7aa21578-3ac3-487e-9447-10c47ca27b7c",
        "51059b82-d08f-4a28-9e2f-2723247cfc1a",
        "62e741a6-a080-4593-b660-9dfcf7456c92",
        "5f653330-4106-40d8-ad7b-b7a4ab23db2a",
        "db08d6af-1e60-4395-afd9-9ed9a417e5e7",
        "bff9d8d4-c877-4c26-8dd4-f887dcfcd262",
        "6006a3f4-3f96-4604-a0b0-00c9ced3141c",
        "dd369206-2ccb-4528-8c73-141d77fe5fa1",
        "b6175807-826a-459f-8a5a-7bff75ff1d36",
        "66225257-b2b3-4577-b889-b8ad87426181",
        "1159d25c-462e-4d86-9343-2e015aa12df2",
        "86b5c251-7c8e-4385-9834-157d6532176c",
    ]
    check_response(request, expected_uuids)


def test_list_length_basic(check_response):
    request = "/structures?filter=elements LENGTH 18"
    expected_uuids = ["b6175807-826a-459f-8a5a-7bff75ff1d36"]
    check_response(request, expected_uuids)


def test_list_length_operators(check_response):
    request = "/structures?filter=elements LENGTH = 17"
    expected_uuids = ["dd369206-2ccb-4528-8c73-141d77fe5fa1"]
    check_response(request, expected_uuids)

    request = "/structures?filter=elements LENGTH >= 17"
    expected_uuids = [
        "dd369206-2ccb-4528-8c73-141d77fe5fa1",
        "b6175807-826a-459f-8a5a-7bff75ff1d36",
    ]
    check_response(request, expected_uuids)

    request = "/structures?filter=cartesian_site_positions LENGTH > 5000"
    expected_uuids = [
        "d99ddab5-026b-45f6-88b7-d81bf0e41988",
        "65e650a8-120d-47d8-afb1-40c81e01d66c",
    ]
    check_response(request, expected_uuids)


def test_list_length_bad_operators(check_error_response):
    """Check NonImplementedError is raised when using a valid,
    but not-supported operator"""
    from optimade.server.config import CONFIG, SupportedBackend

    bad_valid_operator = "!="
    request = f"/structures?filter=elements LENGTH {bad_valid_operator} 2"

    expected_detail = (
        f"Operator {bad_valid_operator} not implemented for LENGTH filter."
        if CONFIG.database_backend == SupportedBackend.MONGODB
        else (
            f"Operator {bad_valid_operator} has not been implemented for the LENGTH "
            "filter."
        )
    )

    check_error_response(
        request,
        expected_status=501,
        expected_title="NotImplementedError",
        expected_detail=expected_detail,
    )


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is not None,
    reason="Test is not for MongoDB",
)
def test_list_has_only(check_error_response):
    # HAS ONLY is not yet implemented
    request = '/structures?filter=elements HAS ONLY "Ac"'
    check_error_response(
        request,
        expected_status=501,
        expected_title="NotImplementedError",
        expected_detail="`set_op_rhs HAS ONLY value_list` has not been implemented.",
    )


def test_list_correlated(check_error_response):
    # Zipped lists are not yet implemented
    request = '/structures?filter=elements:elements_ratios HAS "Ag":"0.2"'
    expected_detail = (
        "Correlated list queries are not supported."
        if os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is not None
        else None
    )
    check_error_response(
        request,
        expected_status=501,
        expected_title="NotImplementedError",
        expected_detail=expected_detail,
    )


def test_saved_extras_is_known(check_response):
    request = "/structures?filter=nsites IS KNOWN AND nsites>=5280"
    expected_uuids = [
        "d99ddab5-026b-45f6-88b7-d81bf0e41988",
        "65e650a8-120d-47d8-afb1-40c81e01d66c",
    ]
    check_response(request, expected_uuids)

    request = "/structures?filter=lattice_vectors IS KNOWN AND nsites>=5280"
    expected_uuids = [
        "d99ddab5-026b-45f6-88b7-d81bf0e41988",
        "65e650a8-120d-47d8-afb1-40c81e01d66c",
    ]
    check_response(request, expected_uuids)


def test_node_columns_is_known(check_response):
    from optimade.server.config import CONFIG, SupportedBackend

    request = (
        f"/structures?filter=_{CONFIG.provider.prefix}_"
        f"{CONFIG.provider_fields['structures'][0]} IS KNOWN AND nsites>=5280"
    )
    expected_uuids = [
        "d99ddab5-026b-45f6-88b7-d81bf0e41988",
        "65e650a8-120d-47d8-afb1-40c81e01d66c",
    ]
    check_response(request, expected_uuids)

    if CONFIG.database_backend != SupportedBackend.MONGODB:
        # Does not work with the Mongo filtertransformer (datetime and IS KNOWN)
        request = "/structures?filter=last_modified IS KNOWN AND nsites>=5280"
        expected_uuids = [
            "d99ddab5-026b-45f6-88b7-d81bf0e41988",
            "65e650a8-120d-47d8-afb1-40c81e01d66c",
        ]
        check_response(request, expected_uuids)

    request = "/structures?filter=id IS KNOWN AND nsites>=5280"
    expected_uuids = [
        "d99ddab5-026b-45f6-88b7-d81bf0e41988",
        "65e650a8-120d-47d8-afb1-40c81e01d66c",
    ]
    check_response(request, expected_uuids)


def test_node_column_fields(check_response, get_valid_id):
    request = f'/structures?filter=id="{get_valid_id}"'
    expected_ids = [str(get_valid_id)]
    check_response(request, expected_ids, expect_id=True)


def test_saved_extras_fields(check_response):
    request = '/structures?filter=chemical_formula_anonymous CONTAINS "A7B4"'
    expected_uuids = [
        "2ebd7c96-cadd-464b-aeda-58e3b86f1347",
        "bf20f3d8-3be9-4336-bbfe-fc13382c61c3",
        "c7b0261c-ed47-48fa-be8a-794ae4e8ce4c",
        "cb40e3b7-067b-4ee4-839d-084824a395e4",
        "fc5a08ae-1026-405f-9fb7-30536cdfc61b",
    ]
    check_response(request, expected_uuids)


def test_string_contains(check_response):
    request = '/structures?filter=chemical_formula_descriptive CONTAINS "Ag4Cl"'
    expected_uuids = [
        "8223bf92-829b-4ba7-9bf6-887f8f21dee8",
        "1d2cf964-9c3a-4be6-92e5-773f4eb93064",
    ]
    check_response(request, expected_uuids)


def test_string_start(check_response):
    request = '/structures?filter=chemical_formula_descriptive STARTS WITH "H"'
    expected_uuids = [
        "02c28e40-0072-418a-9069-7e6ea123ce70",
        "064d0111-4ca9-4511-bdd9-ebb70a47d61d",
        "0b1b5f9d-51dc-473b-94f6-93d85a48ef4c",
        "0e95f602-4da4-4aee-a050-5201c12c8f38",
        "14edc674-37e5-4694-a296-8e59a2879f9f",
        "4d918902-53f6-494a-99f3-859e677f0302",
        "4f6f1c92-4d73-4006-90a0-7bfd59324dbf",
        "545a4e77-b795-411a-be5c-da4a1823a90f",
        "56f7e6b6-afb3-4773-b2b6-e8b5ba5b6683",
        "6a5ad8b8-0922-4ec8-abc0-c5e32123b75b",
        "6c417262-83cd-4fdb-9a9d-7763f1edf808",
        "71bb1432-dc06-4763-9dee-40b11180496b",
        "8384257d-c69f-4e13-9e46-926bbf7f4bc0",
        "8a8cfd2e-1cb0-4d5c-abb5-f80f32534ad2",
        "9359efef-0558-4c52-8169-4f08a5b8692d",
        "aac18afb-722e-49c5-8d66-95d57872ca01",
    ]
    check_response(request, expected_uuids)


def test_string_end(check_response):
    request = '/structures?filter=chemical_formula_descriptive ENDS WITH "0}9"'
    expected_uuids = [
        "7ddb0679-3255-4cea-91be-749e44e9e900",
        "eafac514-e27f-4679-b8bf-d0747af2509d",
        "57244710-298a-42f0-825c-fccd9a025d7d",
    ]
    check_response(request, expected_uuids)


def test_list_has_and(check_response):
    request = '/structures?filter=elements HAS "Na" AND nelements=18'
    expected_uuids = ["b6175807-826a-459f-8a5a-7bff75ff1d36"]
    check_response(request, expected_uuids)


def test_not_or_and_precedence(check_response):
    request = '/structures?filter=NOT elements HAS "Na" AND nelements=5'
    expected_uuids = [
        "705cf9c6-25b3-4720-a079-a342f34712a2",
        "cd2a4ee2-b573-4576-8ede-0b96c6d6bc47",
        "8bbeed07-5c71-4f66-a0b7-f32561fb1797",
        "ab179ba1-84fd-4439-9d50-225b7e32a131",
    ]
    check_response(request, expected_uuids)

    request = '/structures?filter=nelements=5 AND NOT elements HAS "Na"'
    expected_uuids = [
        "705cf9c6-25b3-4720-a079-a342f34712a2",
        "cd2a4ee2-b573-4576-8ede-0b96c6d6bc47",
        "8bbeed07-5c71-4f66-a0b7-f32561fb1797",
        "ab179ba1-84fd-4439-9d50-225b7e32a131",
    ]
    check_response(request, expected_uuids)

    request = '/structures?filter=NOT elements HAS "Na" AND nelements=5 OR nsites>5000'
    expected_ids = [
        "d99ddab5-026b-45f6-88b7-d81bf0e41988",
        "705cf9c6-25b3-4720-a079-a342f34712a2",
        "cd2a4ee2-b573-4576-8ede-0b96c6d6bc47",
        "8bbeed07-5c71-4f66-a0b7-f32561fb1797",
        "ab179ba1-84fd-4439-9d50-225b7e32a131",
        "65e650a8-120d-47d8-afb1-40c81e01d66c",
    ]
    check_response(request, expected_ids)

    request = '/structures?filter=elements HAS "Na" AND nelements>1 AND nsites>5000'
    expected_uuids = [
        "d99ddab5-026b-45f6-88b7-d81bf0e41988",
        "65e650a8-120d-47d8-afb1-40c81e01d66c",
    ]
    check_response(request, expected_uuids)


def test_brackets(check_response):
    request = '/structures?filter=elements HAS "Ga" AND nelements=7 OR nsites=464'
    expected_uuids = [
        "b9e0df95-6029-48cf-a4b4-ddbe0a613572",
        "a20609c5-fa2a-4299-8ebf-e4e97d7cb980",
        "f28033c7-4470-4a1b-a4bc-9e16585c053e",
        "c6755df9-9153-4114-a90e-39590119f4a0",
    ]
    check_response(request, expected_uuids)

    request = (
        '/structures?filter=(elements HAS "Ga" AND nelements=7) OR '
        '(elements HAS "Ga" AND nsites=464)'
    )
    expected_uuids = [
        "a20609c5-fa2a-4299-8ebf-e4e97d7cb980",
        "f28033c7-4470-4a1b-a4bc-9e16585c053e",
    ]
    check_response(request, expected_uuids)


def test_count_filter(caplog):
    """Test EntryCollection.count() when changing filters"""
    from aiida_optimade.routers.structures import STRUCTURES

    STRUCTURES._count = None

    # The _count attribute should be None
    filters = {}
    count_one = STRUCTURES.count(filters=filters)
    assert "self._count is None" in caplog.text
    assert "was not the same as was found in self._count" not in caplog.text
    assert "Using self._count" not in caplog.text
    caplog.clear()
    assert "node_type" in filters  # node_type will be added in the _find method
    assert STRUCTURES._count == {
        "count": count_one,
        "filters": filters,
        "limit": None,
        "offset": None,
    }

    # Changing filters' "node_type" shouldn't result in a new QueryBuilder call
    filters["node_type"] = {"==": "data.core.structure.StructureData."}
    count_two = STRUCTURES.count(filters=filters)
    assert "self._count is None" not in caplog.text
    assert "was not the same as was found in self._count" not in caplog.text
    assert "Using self._count" in caplog.text
    caplog.clear()
    # _find method is not called, so the updated node_type shouldn't change after
    # count()
    assert filters["node_type"] == {"==": "data.core.structure.StructureData."}
    assert count_one == count_two
    assert STRUCTURES._count == {
        "count": count_two,
        "filters": filters,
        "limit": None,
        "offset": None,
    }

    # Changing filters to a non-zero value. This should result in a new QueryBuilder
    # call
    filters = {"extras.optimade.elements": {"contains": ["La", "Ba"]}}
    count_three = STRUCTURES.count(filters=filters)
    assert "self._count is None" not in caplog.text
    assert "filters was not the same as was found in self._count" in caplog.text
    assert "Using self._count" not in caplog.text
    assert count_three == 1
    assert STRUCTURES._count == {
        "count": count_three,
        "filters": filters,
        "limit": None,
        "offset": None,
    }


@pytest.mark.skipif(
    os.getenv("PYTEST_OPTIMADE_CONFIG_FILE") is not None,
    reason="Test is not for MongoDB",
)
def test_querybuilder_calls(caplog, get_valid_id):
    """Check the expected number of QueryBuilder calls are respected"""
    from aiida_optimade.routers.structures import STRUCTURES
    from fastapi.params import Query
    from optimade.server.query_params import EntryListingQueryParams

    def _set_params(params: EntryListingQueryParams) -> EntryListingQueryParams:
        """Utility function to set all query parameter defaults"""
        for attribute, value in params.__dict__.copy().items():
            if isinstance(value, Query):
                setattr(params, attribute, value.default)
        return params

    STRUCTURES._clear_cache()

    optimade_filter = 'elements HAS ALL "La","Ba"'
    expected_data_returned = 1

    # First request will do the following:
    # 1. Query for and set data_available (setting _count to data_available)
    # 2. Query to check extras filter field 'elements', store in cache
    # 3. Query for and set data_returned (setting _count to data_returned)
    # 4. Query for results in DB
    # 5. Reuse _count for more_data_available
    caplog.clear()
    params = _set_params(EntryListingQueryParams(filter=optimade_filter))
    (_, data_returned, _, _, _) = STRUCTURES.find(params=params)
    assert caplog.text.count("Using QueryBuilder") == 4
    assert data_returned == expected_data_returned
    assert "Setting data_available!" in caplog.text  # 1.
    assert "self._count is None" in caplog.text  # 1.
    assert "Checking all extras fields" in caplog.text  # 2.
    assert "Setting data_returned using filter" in caplog.text  # 3.
    assert "filters was not the same as was found in self._count" in caplog.text  # 3.
    assert "Using self._count" in caplog.text  # 5.

    # Perform the exact same request, which will do the following:
    # 1. Reuse _data_available
    # 2. Recognize elements is already in cache of checked extras
    # 3. Reuse set _data_returned
    # 4. Query for results in DB
    # 5. Reuse _count for more_data_available
    caplog.clear()
    (_, data_returned, _, _, _) = STRUCTURES.find(params=params)
    assert caplog.text.count("Using QueryBuilder") == 1
    assert data_returned == expected_data_returned
    assert "Setting data_available!" not in caplog.text  # 1.
    assert "self._count is None" not in caplog.text  # 1., 3., 5.
    assert "Fields have already been checked." in caplog.text  # 2.
    assert "Setting data_returned using filter" not in caplog.text  # 3.
    assert "was not the same as was found in self._count" not in caplog.text  # 5.
    assert "Using self._count" in caplog.text  # 5.

    # Perform request with different filter, but the same extra, which will do the
    # following:
    # 1. Reuse _data_available
    # 2. Recognize elements is already in cache of checked extras
    # 3. Query for and set data_returned (setting _count to data_returned)
    # 4. Query for results in DB
    # 5. Reuse _count for more_data_available
    optimade_filter = 'elements HAS "Ga"'
    expected_data_returned = 14
    caplog.clear()
    params = _set_params(EntryListingQueryParams(filter=optimade_filter))
    (_, data_returned, _, _, _) = STRUCTURES.find(params=params)
    assert caplog.text.count("Using QueryBuilder") == 2
    assert data_returned == expected_data_returned
    assert "Setting data_available!" not in caplog.text  # 1.
    assert "self._count is None" not in caplog.text  # 1., 3., 5.
    assert "Fields have already been checked." in caplog.text  # 2.
    assert "Setting data_returned using filter" in caplog.text  # 3.
    assert "filters was not the same as was found in self._count" in caplog.text  # 3.
    assert "Using self._count" in caplog.text  # 5.

    # Perform request with non-extras field, which will do the following:
    # 1. Reuse _data_available
    # 2. Recognize no extras field is requested
    # 3. Query for and set data_returned (setting _count to data_returned)
    # 4. Query for results in DB
    # 5. Reuse _count for more_data_available
    optimade_filter = f'id="{get_valid_id}"'
    expected_data_returned = 1
    caplog.clear()
    params = _set_params(EntryListingQueryParams(filter=optimade_filter))
    (_, data_returned, _, _, _) = STRUCTURES.find(params=params)
    assert caplog.text.count("Using QueryBuilder") == 2
    assert data_returned == expected_data_returned
    assert "Setting data_available!" not in caplog.text  # 1.
    assert "self._count is None" not in caplog.text  # 1., 3., 5.
    assert "No filter and/or no extras fields requested." in caplog.text  # 2.
    assert "Setting data_returned using filter" in caplog.text  # 3.
    assert "filters was not the same as was found in self._count" in caplog.text  # 3.
    assert "Using self._count" in caplog.text  # 5.
