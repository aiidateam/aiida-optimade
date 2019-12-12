from typing import Union

from fastapi import APIRouter, Depends
from starlette.requests import Request

from aiida import orm

from optimade.models import (
    ErrorResponse,
    ReferenceResource,
    ReferenceResponseMany,
    ReferenceResponseOne,
)

from aiida_optimade.query_params import EntryListingQueryParams, SingleEntryQueryParams
from aiida_optimade.entry_collections import AiidaCollection
from aiida_optimade.mappers import ReferenceMapper
from aiida_optimade.utils import get_backend

from .utils import get_entries, get_single_entry


router = APIRouter()

references = AiidaCollection(
    orm.ReferenceData.objects, ReferenceResource, ReferenceMapper
)


@router.get(
    "/references",
    response_model=Union[ReferenceResponseMany, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Reference"],
)
def get_references(
    request: Request,
    params: EntryListingQueryParams = Depends(),
    backend: orm.implementation.Backend = Depends(get_backend),
):
    return get_entries(
        backend=backend,
        collection=references,
        response=ReferenceResponseMany,
        request=request,
        params=params,
    )


@router.get(
    "/references/{entry_id}",
    response_model=Union[ReferenceResponseOne, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Reference"],
)
def get_single_reference(
    request: Request,
    entry_id: int,
    params: SingleEntryQueryParams = Depends(),
    backend: orm.implementation.Backend = Depends(get_backend),
):
    return get_single_entry(
        backend=backend,
        collection=references,
        entry_id=entry_id,
        response=ReferenceResponseOne,
        request=request,
        params=params,
    )
