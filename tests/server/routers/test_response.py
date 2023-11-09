from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet
    from optimade.models import Response

    from ..conftest import CheckKeys, GetGoodResponse


def _serialize_response_parameters() -> list[tuple[str, type[Response]] | ParameterSet]:
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
    "request_str, ResponseType",
    _serialize_response_parameters(),
)
def test_serialize_response(
    get_good_response: GetGoodResponse, request_str: str, ResponseType: type[Response]
) -> None:
    response = get_good_response(request_str)

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
    request_str: str, get_good_response: GetGoodResponse, check_keys: CheckKeys
) -> None:
    """Check `meta` property in response"""
    from optimade.models import ResponseMeta

    response = get_good_response(request_str)

    assert "meta" in response
    meta_required_keys = ResponseMeta.schema()["required"]
    meta_optional_keys = list(
        set(ResponseMeta.schema()["properties"].keys()) - set(meta_required_keys)
    )
    implemented_optional_keys = ["data_available", "implementation"]

    check_keys(meta_required_keys, response["meta"])
    check_keys(implemented_optional_keys, meta_optional_keys)
    check_keys(implemented_optional_keys, response["meta"])
