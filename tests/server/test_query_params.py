# pylint: disable=missing-function-docstring
import pytest

from optimade.server.config import CONFIG


# Filter
@pytest.mark.skip(
    "Un-skip when a fix for optimade-python-tools issue #102 is in place."
)
def test_custom_field(check_response):
    request = (
        f"/structures?filter=_{CONFIG.provider.prefix}_"
        f'{CONFIG.provider_fields["structures"][0]}'
        '="2019-11-19T18:42:25.844780+01:00"'
    )
    expected_ids = ["1"]
    check_response(request, expected_ids)


def test_id(check_response):
    request = "/structures?filter=id=7"
    expected_ids = ["7"]
    check_response(request, expected_ids)


def test_geq(check_response):
    request = "/structures?filter=nelements>=18"
    expected_ids = ["1048"]
    check_response(request, expected_ids)


def test_gt(check_response):
    request = "/structures?filter=nelements>17"
    expected_ids = ["1048"]
    check_response(request, expected_ids)


def test_gt_none(check_response):
    request = "/structures?filter=nelements>18"
    expected_ids = []
    check_response(request, expected_ids)


def test_rhs_statements(check_response):
    request = "/structures?filter=18<nelements"
    expected_ids = []
    check_response(request, expected_ids)

    request = "/structures?filter=7=id"
    expected_ids = ["7"]
    check_response(request, expected_ids)

    request = "/structures?filter=18<=nelements"
    expected_ids = ["1048"]
    check_response(request, expected_ids)


def test_list_has(check_response):
    request = '/structures?filter=elements HAS "Ga"'
    expected_ids = ["574", "658"]
    check_response(request, expected_ids)


def test_page_limit(check_response):
    request = '/structures?filter=elements HAS "Ge"&page_limit=2'
    expected_ids = ["161", "247", "324", "367", "705"]
    check_response(request, expected_ids, page_limit=2)

    request = '/structures?page_limit=2&filter=elements HAS "Ge"'
    check_response(request, expected_ids, page_limit=2)


def test_list_has_all(check_response):
    request = '/structures?filter=elements HAS ALL "Ge","Na","Al","Cl","O"'
    expected_ids = ["161"]
    check_response(request, expected_ids)


def test_list_has_any(check_response):
    elements = '"La","Ba"'
    request = f"/structures?filter=elements HAS ALL {elements}"
    expected_ids = ["52"]
    check_response(request, expected_ids)

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
    check_response(request, expected_ids)


def test_list_length_basic(check_response):
    request = "/structures?filter=elements LENGTH 18"
    expected_ids = ["1048"]
    check_response(request, expected_ids)


def test_list_length_operators(check_response):
    request = "/structures?filter=elements LENGTH = 17"
    expected_ids = ["1047"]
    check_response(request, expected_ids)

    request = "/structures?filter=elements LENGTH >= 17"
    expected_ids = ["1047", "1048"]
    check_response(request, expected_ids)

    request = "/structures?filter=cartesian_site_positions LENGTH > 5000"
    expected_ids = ["302", "683"]
    check_response(request, expected_ids)


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
            f"Operator {bad_valid_operator} has not been implemented for the LENGTH filter."
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
    expected_ids = ["302", "683"]
    check_response(request, expected_ids)

    request = "/structures?filter=lattice_vectors IS KNOWN AND nsites>=5280"
    expected_ids = ["302", "683"]
    check_response(request, expected_ids)


def test_node_columns_is_known(check_response):
    request = (
        f"/structures?filter=_{CONFIG.provider.prefix}_"
        f"{CONFIG.provider_fields['structures'][0]} IS KNOWN AND nsites>=5280"
    )
    expected_ids = ["302", "683"]
    check_response(request, expected_ids)

    request = "/structures?filter=last_modified IS KNOWN AND nsites>=5280"
    expected_ids = ["302", "683"]
    check_response(request, expected_ids)

    request = "/structures?filter=id IS KNOWN AND nsites>=5280"
    expected_ids = ["302", "683"]
    check_response(request, expected_ids)


def test_node_column_fields(check_response):
    request = '/structures?filter=id="302"'
    expected_ids = ["302"]
    check_response(request, expected_ids)


def test_saved_extras_fields(check_response):
    request = '/structures?filter=chemical_formula_anonymous CONTAINS "A2B3"'
    expected_ids = ["1038", "1045"]
    check_response(request, expected_ids)


def test_string_contains(check_response):
    request = '/structures?filter=chemical_formula_descriptive CONTAINS "Ag4Cl"'
    expected_ids = ["285", "550"]
    check_response(request, expected_ids)


def test_string_start(check_response):
    request = '/structures?filter=chemical_formula_descriptive STARTS WITH "H"'
    expected_ids = ["68", "119", "977"]
    check_response(request, expected_ids)


def test_string_end(check_response):
    request = '/structures?filter=chemical_formula_descriptive ENDS WITH "0}9"'
    expected_ids = ["63", "64", "1080"]
    check_response(request, expected_ids)


def test_list_has_and(check_response):
    request = '/structures?filter=elements HAS "Na" AND nelements=18'
    expected_ids = ["1048"]
    check_response(request, expected_ids)


def test_not_or_and_precedence(check_response):
    request = '/structures?filter=NOT elements HAS "Na" AND nelements=5'
    expected_ids = ["327", "445", "473", "666"]
    check_response(request, expected_ids)

    request = '/structures?filter=nelements=5 AND NOT elements HAS "Na"'
    expected_ids = ["327", "445", "473", "666"]
    check_response(request, expected_ids)

    request = '/structures?filter=NOT elements HAS "Na" AND nelements=5 OR nsites>5000'
    expected_ids = ["302", "327", "445", "473", "666", "683"]
    check_response(request, expected_ids)

    request = '/structures?filter=elements HAS "Na" AND nelements>1 AND nsites>5000'
    expected_ids = ["302", "683"]
    check_response(request, expected_ids)


def test_brackets(check_response):
    request = '/structures?filter=elements HAS "Ga" AND nelements=7 OR nsites=464'
    expected_ids = ["382", "574", "658", "1055"]
    check_response(request, expected_ids)

    request = (
        '/structures?filter=(elements HAS "Ga" AND nelements=7) OR '
        '(elements HAS "Ga" AND nsites=464)'
    )
    expected_ids = ["574", "658"]
    check_response(request, expected_ids)
