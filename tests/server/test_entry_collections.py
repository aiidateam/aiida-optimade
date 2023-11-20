"""Tests for aiida_optimade.entry_collections."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from .conftest import CheckErrorResponse, GetGoodResponse


def test_insert() -> None:
    """Test AiidaCollection.insert() raises NotImplentedError."""
    from aiida_optimade.routers.structures import STRUCTURES

    with pytest.raises(
        NotImplementedError, match="The insert method is not implemented.*"
    ):
        STRUCTURES.insert([])


@pytest.mark.parametrize("attribute", ["data_available", "data_returned"])
def test_causation_errors(attribute: str) -> None:
    """Test CausationError is returned if requesting `data_available` or `data_returned`
    before setting them."""
    from aiida_optimade.common.exceptions import CausationError
    from aiida_optimade.routers.structures import STRUCTURES

    with pytest.raises(
        CausationError, match=f"{attribute} MUST be set before it can be retrieved."
    ):
        getattr(STRUCTURES, attribute)


def test_bad_fields(
    get_good_response: GetGoodResponse,
    check_error_response: CheckErrorResponse,
) -> None:
    """Test a UnknownProviderProperty warning is emitted for unrecognized provider
    fields."""
    from optimade.server.config import CONFIG
    from optimade.server.warnings import UnknownProviderProperty

    # Ignore this unknown provider field
    response = get_good_response(
        "/structures?response_fields=_exmpl_test_provider_field"
    )
    assert (
        response.get("meta", {}).get("warnings", []) == []
    ), f"Warnings found: {response}"

    # Warn about this provider-specific unknown field
    with pytest.warns(UnknownProviderProperty):
        response = get_good_response(
            f"/structures?response_fields=_{CONFIG.provider.prefix}_unknown_provider_"
            "field"
        )
    assert response.get("meta", {}).get(
        "warnings", []
    ), f"No warnings found: {response}"

    # Raise for unknown non-provider field
    bad_field = "unknown_non_provider_field"
    check_error_response(
        request=f"/structures?response_fields={bad_field}",
        expected_status=400,
        expected_title="Bad Request",
        expected_detail=(
            "Unrecognised OPTIMADE field(s) in requested `response_fields`: "
            f"{set([bad_field,])}."
        ),
    )


def test_prepare_query_kwargs() -> None:
    """Check only valid QueryBuilder arguments are allowed for _prepare_query()."""
    from aiida_optimade.routers.structures import STRUCTURES

    with pytest.raises(ValueError):
        STRUCTURES._prepare_query(node_types=[], **{"wrong_arg": "some_value"})


def test_array_sort_type() -> None:
    """Check TypeError is raised if sorting on list value types."""
    from aiida_optimade.routers.structures import STRUCTURES

    with pytest.raises(TypeError):
        STRUCTURES.parse_sort_params("cartesian_site_positions")
