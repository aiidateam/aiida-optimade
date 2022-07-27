from optimade.models import (
    InfoResponse,
    LinksResponse,
    EntryInfoResponse,
    ReferenceResponseMany,
    ReferenceResponseOne,
    StructureResponseMany,
    StructureResponseOne,
)
from optimade.models import ResponseMeta

import pytest


@pytest.mark.parametrize(
    "request_str, ResponseType",
    [
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
    ],
)
def test_serialize_response(get_good_response, request_str, ResponseType):
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
def test_meta_response(request_str, get_good_response, check_keys):
    """Check `meta` property in response"""
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
