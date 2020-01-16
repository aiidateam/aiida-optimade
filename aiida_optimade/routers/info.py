# pylint: disable=missing-function-docstring
import urllib
from typing import Union

from fastapi import APIRouter
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from optimade import __api_version__

from optimade.models import (
    ErrorResponse,
    InfoResponse,
    EntryInfoResponse,
    StructureResource,
)

import aiida_optimade.utils as u


ROUTER = APIRouter()

ENTRY_INFO_SCHEMAS = {"structures": StructureResource.schema}


@ROUTER.get(
    "/info",
    response_model=Union[InfoResponse, ErrorResponse],
    response_model_exclude_unset=False,
    tags=["Info"],
)
def get_info(request: Request):
    from optimade.models import BaseInfoResource, BaseInfoAttributes

    parse_result = urllib.parse.urlparse(str(request.url))
    return InfoResponse(
        meta=u.meta_values(str(request.url), 1, 1, more_data_available=False),
        data=BaseInfoResource(
            attributes=BaseInfoAttributes(
                api_version=f"v{__api_version__}",
                available_api_versions=[
                    {
                        "url": f"{parse_result.scheme}://{parse_result.netloc}",
                        "version": __api_version__,
                    }
                ],
                entry_types_by_format={"json": list(ENTRY_INFO_SCHEMAS.keys())},
                available_endpoints=[
                    "info",
                    "extensions/docs",
                    "extensions/redoc",
                    "extensions/openapi.json",
                ]
                + list(ENTRY_INFO_SCHEMAS.keys()),
            )
        ),
    )


@ROUTER.get(
    "/info/{entry}",
    response_model=Union[EntryInfoResponse, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Info"],
)
def get_info_entry(request: Request, entry: str):
    from optimade.models import EntryInfoResource

    valid_entry_info_endpoints = ENTRY_INFO_SCHEMAS.keys()
    if entry not in valid_entry_info_endpoints:
        raise StarletteHTTPException(
            status_code=404,
            detail=f"Entry info not found for {entry}, valid entry info endpoints are:"
            f" {valid_entry_info_endpoints}",
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
