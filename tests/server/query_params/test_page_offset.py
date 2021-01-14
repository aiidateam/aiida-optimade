"""Test the `page_offset` query parameter"""
# pylint: disable=import-error,protected-access


def test_offset(get_good_response):
    """Apply low offset, comparing two requests with and without offset"""
    page_limit = 5
    request = f"/structures?page_offset=0&page_limit={page_limit}&sort=immutable_id"
    response = get_good_response(request)
    first_response_uuids = [_["attributes"]["immutable_id"] for _ in response["data"]]

    assert len(first_response_uuids) == page_limit

    offset = 2
    request = (
        f"/structures?page_offset={offset}&page_limit={page_limit - offset}"
        "&sort=immutable_id"
    )
    expected_uuids = first_response_uuids[offset:]
    response = get_good_response(request)

    assert len(response["data"]) == len(expected_uuids)
    assert expected_uuids == [_["attributes"]["immutable_id"] for _ in response["data"]]


def test_count_offset(caplog):
    """Test EntryCollection.count() when changing offset"""
    from aiida_optimade.routers.structures import STRUCTURES

    STRUCTURES._count = None

    # The _count attribute should be None
    offset = None
    count_one = STRUCTURES.count(offset=offset)
    assert "self._count is None" in caplog.text
    assert "was not the same as was found in self._count" not in caplog.text
    assert "Using self._count" not in caplog.text
    caplog.clear()
    assert STRUCTURES._count == {
        "count": count_one,
        "filters": {},
        "limit": None,
        "offset": offset,
    }

    # Changing offset to 0 shouldn't result in a new QueryBuilder call
    offset = 0
    count_two = STRUCTURES.count(offset=offset)
    assert "self._count is None" not in caplog.text
    assert "was not the same as was found in self._count" not in caplog.text
    assert "Using self._count" in caplog.text
    caplog.clear()
    assert count_one == count_two
    assert STRUCTURES._count == {
        "count": count_two,
        "filters": {},
        "limit": None,
        "offset": None,  # This shouldn't be updated to 0
    }

    # Changing offset to a non-zero value. This should result in a new QueryBuilder call
    offset = 2
    count_three = STRUCTURES.count(offset=offset)
    assert "self._count is None" not in caplog.text
    assert "offset was not the same as was found in self._count" in caplog.text
    assert "Using self._count" not in caplog.text
    assert count_two == count_three + offset
    assert STRUCTURES._count == {
        "count": count_three,
        "filters": {},
        "limit": None,
        "offset": offset,
    }
