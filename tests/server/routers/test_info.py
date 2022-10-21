from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Iterable, List, Union

    from requests import Response


def test_info_endpoint_attributes(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
    check_keys: "Callable[[List[str], Iterable], None]",
) -> None:
    """Check known properties/attributes for successful response"""
    from optimade.models import BaseInfoAttributes

    response: "Dict[str, Any]" = get_good_response("/info", False)

    assert "data" in response
    assert response["data"]["type"] == "info"
    assert response["data"]["id"] == "/"
    assert "attributes" in response["data"]
    attributes = list(BaseInfoAttributes.schema()["properties"].keys())
    check_keys(attributes, response["data"]["attributes"])


def test_info_structures_endpoint_data(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
    check_keys: "Callable[[List[str], Iterable], None]",
) -> None:
    """Check known properties/attributes for successful response"""
    from optimade.models import EntryInfoResource

    response: "Dict[str, Any]" = get_good_response("/info/structures", False)

    assert "data" in response
    data = EntryInfoResource.schema()["required"]
    check_keys(data, response["data"])


def test_info_structures_sortable(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Check the sortable key is present for all properties"""
    response: "Dict[str, Any]" = get_good_response("/info/structures", False)

    for info_keys in response.get("data", {}).get("properties", {}).values():
        assert "sortable" in info_keys


def test_sortable_values(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Make sure certain properties are and are not sortable"""
    response: "Dict[str, Any]" = get_good_response("/info/structures", False)
    sortable = ["id", "nelements", "nsites"]
    non_sortable = ["species", "lattice_vectors", "dimension_types"]

    for field in sortable:
        sortable_info_value = (
            response.get("data", {})
            .get("properties", {})
            .get(field, {})
            .get("sortable", None)
        )
        assert sortable_info_value is not None
        assert sortable_info_value is True

    for field in non_sortable:
        sortable_info_value = (
            response.get("data", {})
            .get("properties", {})
            .get(field, {})
            .get("sortable", None)
        )
        assert sortable_info_value is not None
        assert sortable_info_value is False


def test_info_structures_unit(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Check the unit key is present for certain properties"""
    response: "Dict[str, Any]" = get_good_response("/info/structures", False)
    unit_fields = ["lattice_vectors", "cartesian_site_positions"]
    for field, info_keys in response.get("data", {}).get("properties", {}).items():
        if field in unit_fields:
            assert "unit" in info_keys, f"Field: {field}"
        else:
            assert "unit" not in info_keys, f"Field: {field}"


def test_provider_fields(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Check the presence of AiiDA-specific fields"""
    from optimade.server.config import CONFIG

    response: "Dict[str, Any]" = get_good_response("/info/structures", False)
    provider_fields = CONFIG.provider_fields.get("structures", [])

    if not provider_fields:
        import warnings

        warnings.warn("No provider-specific fields found for 'structures'!")
        return

    for field in provider_fields:
        updated_field_name = f"_{CONFIG.provider.prefix}_{field}"
        assert updated_field_name in response.get("data", {}).get("properties", {})

        for static_key in ["description", "sortable"]:
            assert static_key in response.get("data", {}).get("properties", {}).get(
                updated_field_name, {}
            )


@pytest.mark.skip("References has not yet been implemented")
def test_info_references_endpoint_data(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
    check_keys: "Callable[[List[str], Iterable], None]",
) -> None:
    """Check known properties/attributes for successful response"""
    from optimade.models import EntryInfoResource

    response: "Dict[str, Any]" = get_good_response("/info/reference", False)

    assert "data" in response
    data = EntryInfoResource.schema()["required"]
    check_keys(data, response["data"])
