from optimade import __api_version__


def test_versions_endpoint(get_good_response):
    """Check known content for a successful response"""
    response = get_good_response("/versions")

    assert response.text == f"version\n{__api_version__.replace('v', '').split('.')[0]}"
    assert "text/csv" in response.headers.get("content-type")
    assert "header=present" in response.headers.get("content-type")
