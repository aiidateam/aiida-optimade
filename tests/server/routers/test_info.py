import pytest
from optimade.models import BaseInfoAttributes, EntryInfoResource


def test_info_endpoint_attributes(get_good_response, check_keys):
    """Check known properties/attributes for successful response"""
    response = get_good_response("/info")

    assert "data" in response
    assert response["data"]["type"] == "info"
    assert response["data"]["id"] == "/"
    assert "attributes" in response["data"]
    attributes = list(BaseInfoAttributes.schema()["properties"].keys())
    check_keys(attributes, response["data"]["attributes"])


def test_info_structures_endpoint_data(get_good_response, check_keys):
    """Check known properties/attributes for successful response"""
    response = get_good_response("/info/structures")

    assert "data" in response
    data = EntryInfoResource.schema()["required"]
    check_keys(data, response["data"])


def test_info_structures_sortable(get_good_response):
    """Check the sortable key is present for all properties"""
    response = get_good_response("/info/structures")

    for info_keys in response.get("data", {}).get("properties", {}).values():
        assert "sortable" in info_keys


def test_sortable_values(get_good_response):
    """Make sure certain properties are and are not sortable"""
    response = get_good_response("/info/structures")
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


def test_info_structures_unit(get_good_response):
    """Check the unit key is present for certain properties"""
    response = get_good_response("/info/structures")
    unit_fields = ["lattice_vectors", "cartesian_site_positions"]
    for field, info_keys in response.get("data", {}).get("properties", {}).items():
        if field in unit_fields:
            assert "unit" in info_keys, f"Field: {field}"
        else:
            assert "unit" not in info_keys, f"Field: {field}"


def test_provider_fields(get_good_response):
    """Check the presence of AiiDA-specific fields"""
    from optimade.server.config import CONFIG

    response = get_good_response("/info/structures")
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
def test_info_references_endpoint_data(get_good_response, check_keys):
    """Check known properties/attributes for successful response"""
    response = get_good_response("/info/reference")

    assert "data" in response
    data = EntryInfoResource.schema()["required"]
    check_keys(data, response["data"])
