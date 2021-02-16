import functools
import urllib

from typing import Union, List

from fastapi import HTTPException, Request

from optimade.models import (
    EntryResponseMany,
    EntryResponseOne,
    EntryResource,
    ToplevelLinks,
)
from optimade.server.config import CONFIG
from optimade.server.entry_collections.mongo import MongoCollection
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.routers.utils import meta_values

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


def handle_response_fields(
    results: Union[List[EntryResource], EntryResource],
    fields: set,
    collection: AiidaCollection,
) -> dict:
    """Prune results to only include queried fields (from `response_fields`)"""
    if not isinstance(results, list):
        results = [results]
    non_attribute_fields = collection.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS
    top_level = {_ for _ in non_attribute_fields if _ in fields}
    attribute_level = fields - non_attribute_fields
    new_results = []
    while results:
        entry = results.pop(0)
        new_entry = entry.dict(
            exclude=top_level, exclude_unset=True, exclude_none=False, by_alias=True
        )
        for field in attribute_level:
            if field in new_entry["attributes"]:
                del new_entry["attributes"][field]
        if not new_entry["attributes"]:
            del new_entry["attributes"]
        new_results.append(new_entry)
    return new_results


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
    ) = collection.find(params)

    pagination = handle_pagination(
        request=request, more_data_available=more_data_available, nresults=len(results)
    )

    if fields:
        results = handle_response_fields(results, fields, collection)

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
    ) = collection.find(params)

    if more_data_available:
        raise HTTPException(
            status_code=500,
            detail="more_data_available MUST be False for single entry response, "
            f"however it is {more_data_available}",
        )

    if fields and results is not None:
        results = handle_response_fields(results, fields, collection)[0]

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
