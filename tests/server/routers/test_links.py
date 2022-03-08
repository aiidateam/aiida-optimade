def test_links(get_good_response):
    """Check /links for successful response"""
    response = get_good_response("/links")

    assert "data" in response
