from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Union

    from requests import Response


def test_links(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Check /links for successful response"""
    response = get_good_response("/links", False)
    assert isinstance(response, dict)

    assert "data" in response
