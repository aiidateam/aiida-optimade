from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..conftest import GetGoodResponse


def test_versions_endpoint(get_good_response: GetGoodResponse) -> None:
    """Check known content for a successful response"""
    from optimade import __api_version__

    response = get_good_response("/versions", raw=True)

    assert not isinstance(response, dict)

    assert response.text == f"version\n{__api_version__.replace('v', '').split('.')[0]}"
    assert "text/csv" in response.headers.get("content-type")
    assert "header=present" in response.headers.get("content-type")
