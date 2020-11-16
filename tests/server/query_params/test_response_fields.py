def test_provider_fields(get_good_response):
    """Ensure provider fields can be requested"""
    from optimade.server.config import CONFIG

    provider_specific_field = (
        f"_{CONFIG.provider.prefix}_"
        f"{CONFIG.provider_fields.get('structures', ['ctime'])[0]}"
    )
    request = f"/structures?response_fields={provider_specific_field}"
    response = get_good_response(request)

    returned_attributes = set()
    for _ in response.get("data", []):
        returned_attributes |= set(_.get("attributes", {}).keys())
    assert returned_attributes == {
        provider_specific_field,
    }


def test_non_provider_fields(get_good_response):
    """Ensure provider fields are excluded when not requested"""
    non_provider_specific_field = "elements"
    request = f"/structures?response_fields={non_provider_specific_field}"
    response = get_good_response(request)

    returned_attributes = set()
    for _ in response.get("data", []):
        returned_attributes |= set(_.get("attributes", {}).keys())
    assert returned_attributes == {
        non_provider_specific_field,
    }


def test_wrong_alias_provider_fields(get_good_response):
    """Ensure wrongly aliased provider fields are disregarded as unknown field"""
    from optimade.server.config import CONFIG

    wrongly_aliased_provider_field = CONFIG.provider_fields.get("structures", [])
    request = f"/structures?response_fields={','.join(wrongly_aliased_provider_field)}"
    response = get_good_response(request)

    returned_attributes = set()
    for _ in response.get("data", []):
        returned_attributes |= set(_.get("attributes", {}).keys())
    assert returned_attributes == set()
