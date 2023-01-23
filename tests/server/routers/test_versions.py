from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Union

    from httpx import Response


def test_versions_endpoint(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Check known content for a successful response"""
    from httpx import Response
    from optimade import __api_version__

    response = get_good_response("/versions", True)
    assert isinstance(response, Response)

    assert (
        response.text
        == f"version\n{__api_version__.replace('v', '').split('.', maxsplit=1)[0]}"
    )
    assert "text/csv" in response.headers.get("content-type", "")
    assert "header=present" in response.headers.get("content-type", "")
