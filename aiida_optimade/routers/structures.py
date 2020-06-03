# pylint: disable=missing-function-docstring
from typing import Union

from fastapi import APIRouter, Depends, Request

from aiida.orm import StructureData

from optimade.models import (
    ErrorResponse,
    StructureResponseMany,
    StructureResponseOne,
)
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams

from aiida_optimade.entry_collections import AiidaCollection
from aiida_optimade.mappers import StructureMapper
from aiida_optimade.models import StructureResource

from .utils import get_entries, get_single_entry, close_session


ROUTER = APIRouter(redirect_slashes=True)

STRUCTURES = AiidaCollection(StructureData, StructureResource, StructureMapper)


@ROUTER.get(
    "/structures",
    response_model=Union[StructureResponseMany, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Structures"],
)
@close_session
def get_structures(request: Request, params: EntryListingQueryParams = Depends()):
    return get_entries(
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
@close_session
def get_single_structure(
    request: Request, entry_id: int, params: SingleEntryQueryParams = Depends()
):
    return get_single_entry(
        collection=STRUCTURES,
        entry_id=entry_id,
        response=StructureResponseOne,
        request=request,
        params=params,
    )
