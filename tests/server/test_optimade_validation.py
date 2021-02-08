def test_with_validator(remote_client):
    """Validate server"""
    from optimade.validator import ImplementationValidator

    validator = ImplementationValidator(client=remote_client, verbosity=5)

    validator.validate_implementation()
    assert validator.valid


def test_versioned_base_urls(client):
    """Test all expected versioned base URLs responds with 200"""
    try:
        import simplejson as json
    except ImportError:
        import json

    from optimade.server.routers.utils import BASE_URL_PREFIXES

    valid_endpoints = ("/info", "/links", "/structures")

    for version in BASE_URL_PREFIXES.values():
        for endpoint in valid_endpoints:
            response = client.get(url=version + endpoint)
            json_response = response.json()

            assert response.status_code == 200, (
                f"Request to {response.url} failed: "
                f"{json.dumps(json_response, indent=2)}"
            )
            assert "meta" in json_response, (
                "Mandatory 'meta' top-level field not found in request to "
                f"{response.url}. Response: {json.dumps(json_response, indent=2)}"
            )
