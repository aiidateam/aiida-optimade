import functools
import urllib.parse
from typing import TYPE_CHECKING

from fastapi import HTTPException
from optimade.models import ToplevelLinks
from optimade.server.config import CONFIG
from optimade.server.routers.utils import (
    get_base_url,
    handle_response_fields,
    meta_values,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Type, Union

    from fastapi import Request
    from optimade.models import EntryResponseMany, EntryResponseOne
    from optimade.server.entry_collections.mongo import MongoCollection
    from optimade.server.query_params import (
        EntryListingQueryParams,
        SingleEntryQueryParams,
    )

    from aiida_optimade.entry_collections import AiidaCollection


def handle_pagination(
    request: "Request", more_data_available: bool, nresults: int
) -> dict:
    """Handle pagination for request with number of results equal nresults"""
    pagination = {}

    # "prev"
    parse_result = urllib.parse.urlparse(str(request.url))
    base_url = get_base_url(parse_result)
    query = urllib.parse.parse_qs(parse_result.query)
    query["page_offset"] = int(query.get("page_offset", ["0"])[0]) - int(
        query.get("page_limit", [CONFIG.page_limit])[0]
    )
    urlencoded_prev = None
    if query["page_offset"] > 0:
        urlencoded_prev = urllib.parse.urlencode(query, doseq=True)
    elif query["page_offset"] == 0 or abs(query["page_offset"]) < int(
        query.get("page_limit", [CONFIG.page_limit])[0]
    ):
        prev_query = query.copy()
        prev_query.pop("page_offset")
        urlencoded_prev = urllib.parse.urlencode(prev_query, doseq=True)
    if urlencoded_prev:
        pagination["prev"] = f"{base_url}{parse_result.path}"
        pagination["prev"] += f"?{urlencoded_prev}"

    # "next"
    if more_data_available:
        query["page_offset"] = (
            int(query.get("page_offset", 0))
            + nresults
            + int(query.get("page_limit", [CONFIG.page_limit])[0])
        )
        urlencoded_next = urllib.parse.urlencode(query, doseq=True)
        pagination["next"] = f"{base_url}{parse_result.path}"
        if urlencoded_next:
            pagination["next"] += f"?{urlencoded_next}"
    else:
        pagination["next"] = None

    return pagination


def get_entries(
    collection: "Union[AiidaCollection, MongoCollection]",
    response: "Type[EntryResponseMany]",
    request: "Request",
    params: "EntryListingQueryParams",
) -> "EntryResponseMany":
    """Generalized /{entry} endpoint getter"""
    (
        results,
        data_returned,
        more_data_available,
        fields,
        include_fields,
    ) = collection.find(params)

    if not isinstance(results, list):
        raise TypeError("Expected a list of results.")

    pagination = handle_pagination(
        request=request, more_data_available=more_data_available, nresults=len(results)
    )

    if fields or include_fields:
        results = handle_response_fields(
            results=results, exclude_fields=fields, include_fields=include_fields
        )

    return response(
        links=ToplevelLinks(**pagination),
        data=results,
        meta=meta_values(
            url=request.url,
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
            schema=CONFIG.schema_url,
        ),
    )


def get_single_entry(
    collection: "Union[AiidaCollection, MongoCollection]",
    entry_id: str,
    response: "Type[EntryResponseOne]",
    request: "Request",
    params: "SingleEntryQueryParams",
) -> "EntryResponseOne":
    """Generalized /{entry}/{entry_id} endpoint getter"""
    setattr(params, "filter", f'id="{entry_id}"')
    (
        results,
        data_returned,
        more_data_available,
        fields,
        include_fields,
    ) = collection.find(params)

    if more_data_available or isinstance(results, list):
        raise HTTPException(
            status_code=500,
            detail="more_data_available MUST be False for single entry response, "
            f"however it is {more_data_available}",
        )

    if (fields or include_fields) and results is not None:
        results = handle_response_fields(
            results=results, exclude_fields=fields, include_fields=include_fields
        )[0]

    return response(
        links=ToplevelLinks(next=None),
        data=results,
        meta=meta_values(
            url=request.url,
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
            schema=CONFIG.schema_url,
        ),
    )


def close_session(func):
    """Close AiiDA SQLAlchemy session

    Since the middleware creates multiple threads when awaiting responses, it cannot be
    used. Instead, this decorator can be used for router endpoints to close the AiiDA
    SQLAlchemy global scoped session after the response has been created. This is
    needed, since AiiDA's QueryBuilder uses a SQLAlchemy global scoped session no
    matter the backend.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            value = func(*args, **kwargs)
        finally:
            from aiida.manage.manager import (  # pylint: disable=import-outside-toplevel
                get_manager,
            )

            get_manager().get_backend().close()
        return value

    return wrapper
