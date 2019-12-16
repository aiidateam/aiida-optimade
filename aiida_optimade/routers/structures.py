# pylint: disable=missing-function-docstring
from typing import Union

from fastapi import APIRouter, Depends
from starlette.requests import Request

from aiida import orm

from optimade.models import (
    ErrorResponse,
    StructureResource,
    StructureResponseMany,
    StructureResponseOne,
)

from aiida_optimade.query_params import EntryListingQueryParams, SingleEntryQueryParams
from aiida_optimade.entry_collections import AiidaCollection
from aiida_optimade.mappers import StructureMapper
from aiida_optimade.utils import get_backend

from .utils import get_entries, get_single_entry


ROUTER = APIRouter()

structures = AiidaCollection(orm.StructureData, StructureResource, StructureMapper)


@ROUTER.get(
    "/structures",
    response_model=Union[StructureResponseMany, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Structures"],
)
def get_structures(
    request: Request,
    params: EntryListingQueryParams = Depends(),
    backend: orm.implementation.Backend = Depends(get_backend),
):
    return get_entries(
        backend=backend,
        collection=STRUCTURES,
        response=StructureResponseMany,
        request=request,
        params=params,
    )


@ROUTER.get(
    "/structures/{entry_id}",
    response_model=Union[StructureResponseOne, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Structures"],
)
def get_single_structure(
    request: Request,
    entry_id: int,
    params: SingleEntryQueryParams = Depends(),
    backend: orm.implementation.Backend = Depends(get_backend),
):
    return get_single_entry(
        backend=backend,
        collection=STRUCTURES,
        entry_id=entry_id,
        response=StructureResponseOne,
        request=request,
        params=params,
    )
