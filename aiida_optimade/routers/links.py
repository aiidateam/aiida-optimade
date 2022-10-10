"""Reusing the optimade-python-tools /links endpoint"""
# pylint: disable=missing-function-docstring
from typing import Union

from fastapi import APIRouter, Depends, Request
from optimade.models import ErrorResponse, LinksResource, LinksResponse
from optimade.server.config import CONFIG
from optimade.server.entry_collections.mongo import MongoCollection
from optimade.server.mappers import LinksMapper
from optimade.server.query_params import EntryListingQueryParams
from optimade.server.routers.utils import get_entries

ROUTER = APIRouter(redirect_slashes=True)

LINKS = MongoCollection(
    name=CONFIG.links_collection,
    resource_cls=LinksResource,
    resource_mapper=LinksMapper,
)


@ROUTER.get(
    "/links",
    response_model=Union[LinksResponse, ErrorResponse],
    response_model_exclude_unset=True,
    response_model_exclude_none=False,
    tags=["Links"],
)
def get_links(request: Request, params: EntryListingQueryParams = Depends()):
    return get_entries(
        collection=LINKS, response=LinksResponse, request=request, params=params
    )
