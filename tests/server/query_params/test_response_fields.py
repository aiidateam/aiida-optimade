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


def test_wrong_alias_provider_fields(check_error_response):
    """Ensure wrongly aliased provider fields raise a 400 Bad Request"""
    from optimade.server.config import CONFIG

    wrongly_aliased_provider_field = CONFIG.provider_fields.get("structures", [])
    request = f"/structures?response_fields={','.join(wrongly_aliased_provider_field)}"
    check_error_response(
        request,
        expected_status=400,
        expected_title="Bad Request",
        expected_detail=(
            "Unrecognised OPTIMADE field(s) in requested `response_fields`: "
            f"{set(wrongly_aliased_provider_field)}."
        ),
    )
