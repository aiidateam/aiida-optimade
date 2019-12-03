import urllib
from typing import Union

from fastapi import APIRouter
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from optimade.models import (
    ErrorResponse,
    InfoResponse,
    EntryInfoResponse,
    StructureResource,
)

from aiida_optimade.config import CONFIG
import aiida_optimade.utils as u


router = APIRouter()

ENTRY_INFO_SCHEMAS = {"structures": StructureResource.schema}


@router.get(
    "/info",
    response_model=Union[InfoResponse, ErrorResponse],
    response_model_skip_defaults=False,
    tags=["Info"],
)
def get_info(request: Request):
    from optimade.models import BaseInfoResource, BaseInfoAttributes

    parse_result = urllib.parse.urlparse(str(request.url))
    return InfoResponse(
        meta=u.meta_values(str(request.url), 1, 1, more_data_available=False),
        data=BaseInfoResource(
            attributes=BaseInfoAttributes(
                api_version=CONFIG.version,
                available_api_versions=[
                    {
                        "url": f"{parse_result.scheme}://{parse_result.netloc}",
                        "version": f"{CONFIG.version[1:]}",
                    }
                ],
                entry_types_by_format={"json": ["structures"]},
                available_endpoints=[
                    "info",
                    "structures",
                    "extensions/docs",
                    "extensions/redoc",
                    "extensions/openapi.json",
                ],
            )
        ),
    )


@router.get(
    "/info/{entry}",
    response_model=Union[EntryInfoResponse, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Info", "Structure"],
)
def get_info_entry(request: Request, entry: str):
    from optimade.models import EntryInfoResource

    valid_entry_info_endpoints = {"structures"}
    if entry not in valid_entry_info_endpoints:
        raise StarletteHTTPException(
            status_code=404,
            detail=f"Entry info not found for {entry}, valid entry info endpoints are: {valid_entry_info_endpoints}",
        )

    schema = ENTRY_INFO_SCHEMAS[entry]()
    queryable_properties = {"id", "type", "attributes"}
    properties, _ = u.retrieve_queryable_properties(schema, queryable_properties)

    output_fields_by_format = {"json": list(properties.keys())}

    return EntryInfoResponse(
        meta=u.meta_values(str(request.url), 1, 1, more_data_available=False),
        data=EntryInfoResource(
            formats=list(output_fields_by_format.keys()),
            description=schema.get(
                "description",
                "Endpoint to represent AiiDA Nodes in the OPTiMaDe format",
            ),
            properties=properties,
            output_fields_by_format=output_fields_by_format,
        ),
    )
