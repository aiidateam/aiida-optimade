"""Test the `page_limit` query parameter"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

    from ..conftest import CheckErrorResponse, GetGoodResponse


def test_limit(get_good_response: GetGoodResponse) -> None:
    """Check page_limit is respected"""
    page_limit = [5, 10]
    for limit in page_limit:
        request = f"/structures?page_limit={limit}"
        response = get_good_response(request)

        assert len(response["data"]) == limit


def test_count_limit(caplog: pytest.LogCaptureFixture) -> None:
    """Test EntryCollection.count() when changing limit"""
    from aiida_optimade.routers.structures import STRUCTURES

    STRUCTURES._count = None

    # The _count attribute should be None
    limit = None
    count_one = STRUCTURES.count(limit=limit)
    assert "self._count is None" in caplog.text
    assert "was not the same as was found in self._count" not in caplog.text
    assert "Using self._count" not in caplog.text
    caplog.clear()
    assert STRUCTURES._count == {
        "count": count_one,
        "filters": {},
        "limit": limit,
        "offset": None,
    }

    # Changing limit to an int. This should result in a new QueryBuilder call
    limit = 5
    count_two = STRUCTURES.count(limit=limit)
    assert "self._count is None" not in caplog.text
    assert "limit was not the same as was found in self._count" in caplog.text
    assert "Using self._count" not in caplog.text
    assert count_two == limit
    caplog.clear()
    assert STRUCTURES._count == {
        "count": count_two,
        "filters": {},
        "limit": limit,
        "offset": None,
    }

    # Keeping the same limit. This should not result in a new QueryBuilder call
    count_three = STRUCTURES.count(limit=limit)
    assert "self._count is None" not in caplog.text
    assert "was not the same as was found in self._count" not in caplog.text
    assert "Using self._count" in caplog.text
    assert count_two == count_three
    assert STRUCTURES._count == {
        "count": count_three,
        "filters": {},
        "limit": limit,
        "offset": None,
    }


def test_page_limit_max(
    get_good_response: GetGoodResponse, check_error_response: CheckErrorResponse
) -> None:
    """Ensure the configuration page_limit_max is respected"""
    from optimade.server.config import CONFIG

    request = f"/structures?page_limit={CONFIG.page_limit_max}"
    response = get_good_response(request)
    assert len(response["data"]) == CONFIG.page_limit_max

    request = f"/structures?page_limit={CONFIG.page_limit_max + 1}"
    check_error_response(
        request,
        expected_status=403,
        expected_title="Forbidden",
        expected_detail=(
            f"Max allowed page_limit is {CONFIG.page_limit_max}, you requested "
            f"{CONFIG.page_limit_max + 1}"
        ),
    )
