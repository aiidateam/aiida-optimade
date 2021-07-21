import functools
import urllib.parse

from typing import Union

from fastapi import HTTPException, Request

from optimade.models import (
    EntryResponseMany,
    EntryResponseOne,
    ToplevelLinks,
)
from optimade.server.config import CONFIG
from optimade.server.entry_collections.mongo import MongoCollection
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.routers.utils import handle_response_fields, meta_values

from aiida_optimade.entry_collections import AiidaCollection


def handle_pagination(
    request: Request, more_data_available: bool, nresults: int
) -> dict:
    """Handle pagination for request with number of results equal nresults"""
    from optimade.server.routers.utils import get_base_url

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
    collection: Union[AiidaCollection, MongoCollection],
    response: EntryResponseMany,
    request: Request,
    params: EntryListingQueryParams,
) -> EntryResponseMany:
    """Generalized /{entry} endpoint getter"""
    (
        results,
        data_returned,
        more_data_available,
        fields,
        include_fields,
    ) = collection.find(params)

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
        ),
    )


def get_single_entry(
    collection: Union[AiidaCollection, MongoCollection],
    entry_id: str,
    response: EntryResponseOne,
    request: Request,
    params: SingleEntryQueryParams,
) -> EntryResponseOne:
    """Generalized /{entry}/{entry_id} endpoint getter"""
    params.filter = f'id="{entry_id}"'
    (
        results,
        data_returned,
        more_data_available,
        fields,
        include_fields,
    ) = collection.find(params)

    if more_data_available:
        raise HTTPException(
            status_code=500,
            detail="more_data_available MUST be False for single entry response, "
            f"however it is {more_data_available}",
        )

    if fields or include_fields and results is not None:
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
            from aiida.manage.manager import get_manager

            get_manager().get_backend().get_session().close()
        return value

    return wrapper
