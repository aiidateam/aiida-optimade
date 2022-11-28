from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable, Dict, Iterable, List, Tuple, Type, Union

    from _pytest.mark.structures import ParameterSet
    from pydantic import BaseModel
    from requests import Response


def parameters_for_serialize_response() -> "List[Union[Tuple[str, Type[BaseModel]], ParameterSet]]":  # pylint: disable=line-too-long
    """Return the list of parameters for `test_serialize_response`."""
    from optimade.models import (
        EntryInfoResponse,
        InfoResponse,
        LinksResponse,
        ReferenceResponseMany,
        ReferenceResponseOne,
        StructureResponseMany,
        StructureResponseOne,
    )

    return [
        ("/info", InfoResponse),
        ("/info/structures", EntryInfoResponse),
        ("/links", LinksResponse),
        ("/structures", StructureResponseMany),
        ("/structures/0", StructureResponseOne),
        pytest.param(
            "/references",
            ReferenceResponseMany,
            marks=pytest.mark.xfail(reason="References has not yet been implemented"),
        ),
        pytest.param(
            "/references/dijkstra1968",
            ReferenceResponseOne,
            marks=pytest.mark.xfail(reason="References has not yet been implemented"),
        ),
        pytest.param(
            "/references/dummy/20.19",
            ReferenceResponseOne,
            marks=pytest.mark.xfail(reason="References has not yet been implemented"),
        ),
    ]


@pytest.mark.parametrize(
    "request_str, ResponseType", parameters_for_serialize_response()
)
def test_serialize_response(
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
    request_str: str,
    ResponseType: "Type[BaseModel]",  # pylint: disable=invalid-name
) -> None:
    """Test serializing responses."""
    response: "Dict[str, Any]" = get_good_response(request_str, False)
    ResponseType(**response)


@pytest.mark.parametrize(
    "request_str",
    [
        "/info",
        "/info/structures",
        "/links",
        "/structures",
        "structures/0",
        pytest.param(
            "/references",
            marks=pytest.mark.xfail(reason="References has not yet been implemented"),
        ),
    ],
)
def test_meta_response(
    request_str: str,
    get_good_response: "Callable[[str, bool], Union[Dict[str, Any], Response]]",
    check_keys: "Callable[[List[str], Iterable], None]",
) -> None:
    """Check `meta` property in response"""
    from optimade.models import ResponseMeta

    response: "Dict[str, Any]" = get_good_response(request_str, False)

    assert "meta" in response
    meta_required_keys = ResponseMeta.schema()["required"]
    meta_optional_keys = list(
        set(ResponseMeta.schema()["properties"].keys()) - set(meta_required_keys)
    )
    implemented_optional_keys = ["data_available", "implementation"]

    check_keys(meta_required_keys, response["meta"])
    check_keys(implemented_optional_keys, meta_optional_keys)
    check_keys(implemented_optional_keys, response["meta"])
