def test_last_modified(get_good_response):
    """Ensure last_modified does not change upon requests"""
    from time import sleep

    request = "/structures"

    first_response = get_good_response(request)
    sleep(2)
    second_response = get_good_response(request)

    assert [_["id"] for _ in first_response["data"]] == [
        _["id"] for _ in second_response["data"]
    ]
    assert [_["attributes"]["last_modified"] for _ in first_response["data"]] == [
        _["attributes"]["last_modified"] for _ in second_response["data"]
    ]
