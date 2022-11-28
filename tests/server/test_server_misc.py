from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable, Dict, Union

    from requests import Response


def test_last_modified(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
) -> None:
    """Ensure last_modified does not change upon requests"""
    from time import sleep

    request = "/structures"

    first_response: "Dict[str, Any]" = get_good_response(request, False)
    sleep(2)
    second_response: "Dict[str, Any]" = get_good_response(request, False)

    assert [_["id"] for _ in first_response["data"]] == [
        _["id"] for _ in second_response["data"]
    ]
    assert [_["attributes"]["last_modified"] for _ in first_response["data"]] == [
        _["attributes"]["last_modified"] for _ in second_response["data"]
    ]
