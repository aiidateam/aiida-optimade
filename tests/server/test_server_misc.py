from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Union

    from httpx import Response


def test_last_modified(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Ensure last_modified does not change upon requests"""
    from time import sleep

    request = "/structures"

    first_response = get_good_response(request, False)
    assert isinstance(first_response, dict)
    sleep(2)
    second_response = get_good_response(request, False)
    assert isinstance(second_response, dict)

    assert [_["id"] for _ in first_response["data"]] == [
        _["id"] for _ in second_response["data"]
    ]
    assert [_["attributes"]["last_modified"] for _ in first_response["data"]] == [
        _["attributes"]["last_modified"] for _ in second_response["data"]
    ]
