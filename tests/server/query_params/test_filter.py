# pylint: disable=missing-function-docstring
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
    request = f"/structures?filter=id={get_valid_id}"
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

    request = f"/structures?filter={get_valid_id}=id"
    expected_ids = [str(get_valid_id)]
    check_response(request, expected_ids, expect_id=True)

    request = "/structures?filter=18<=nelements"
    expected_uuids = ["b6175807-826a-459f-8a5a-7bff75ff1d36"]
    check_response(request, expected_uuids)


def test_list_has(check_response):
    request = '/structures?filter=elements HAS "Ga"'
    expected_uuids = [
        "a20609c5-fa2a-4299-8ebf-e4e97d7cb980",
        "f28033c7-4470-4a1b-a4bc-9e16585c053e",
    ]
    check_response(request, expected_uuids)


def test_page_limit(check_response):
    request = '/structures?filter=elements HAS "Ge"&page_limit=2'
    expected_uuids = [
        "254947de-54c8-4cdb-afc5-1cee237f9f98",
        "c51a7153-160e-42c0-a9eb-6f5fef95971b",
        "68c20029-3785-446c-9b4d-290de2366e71",
        "bfdf11e9-bc59-422d-8d99-1d7b3ba7d4d9",
        "db08d6af-1e60-4395-afd9-9ed9a417e5e7",
    ]
    check_response(request, expected_uuids, page_limit=2)

    request = '/structures?page_limit=2&filter=elements HAS "Ge"'
    check_response(request, expected_uuids, page_limit=2)


def test_list_has_all(check_response):
    request = '/structures?filter=elements HAS ALL "Ge","Na","Al","Cl","O"'
    expected_uuids = ["254947de-54c8-4cdb-afc5-1cee237f9f98"]
    check_response(request, expected_uuids)


def test_warnings_for_assemblies(check_response):
    """Check a NotImplementedWarning is raised for 'assemblies'"""
    from aiida_optimade.common.warnings import NotImplementedWarning

    request = "/structures?filter=nelements>=18"
    expected_uuids = ["b6175807-826a-459f-8a5a-7bff75ff1d36"]

    with pytest.warns(
        NotImplementedWarning, match="Parsing optional attribute 'assemblies'",
    ):
        check_response(request, expected_uuids)


def test_list_has_any(check_response):
    elements = '"La","Ba"'
    request = f"/structures?filter=elements HAS ALL {elements}"
    expected_uuids = ["c8368624-e49a-46ad-aef7-daaee4ff89e3"]
    check_response(request, expected_uuids)

    request = f"/structures?filter=elements HAS ANY {elements}"
    expected_uuids = [
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
    bad_valid_operator = "!="
    request = f"/structures?filter=elements LENGTH {bad_valid_operator} 2"
    check_error_response(
        request,
        expected_status=501,
        expected_title="NotImplementedError",
        expected_detail=(
            f"Operator {bad_valid_operator} has not been implemented for the LENGTH "
            "filter."
        ),
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
    check_error_response(
        request, expected_status=501, expected_title="NotImplementedError"
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
    from optimade.server.config import CONFIG

    request = (
        f"/structures?filter=_{CONFIG.provider.prefix}_"
        f"{CONFIG.provider_fields['structures'][0]} IS KNOWN AND nsites>=5280"
    )
    expected_uuids = [
        "d99ddab5-026b-45f6-88b7-d81bf0e41988",
        "65e650a8-120d-47d8-afb1-40c81e01d66c",
    ]
    check_response(request, expected_uuids)

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
    request = '/structures?filter=chemical_formula_anonymous CONTAINS "A2B3"'
    expected_uuids = [
        "14d11c49-46d5-4575-bc52-14a017f8346b",
        "6006a3f4-3f96-4604-a0b0-00c9ced3141c",
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
        "8384257d-c69f-4e13-9e46-926bbf7f4bc0",
        "0e95f602-4da4-4aee-a050-5201c12c8f38",
        "14edc674-37e5-4694-a296-8e59a2879f9f",
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
