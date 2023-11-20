from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..conftest import GetGoodResponse


def test_links(get_good_response: GetGoodResponse) -> None:
    """Check /links for successful response"""
    response = get_good_response("/links")

    assert "data" in response
