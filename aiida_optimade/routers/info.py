# pylint: disable=missing-function-docstring
import urllib
from typing import Union

from fastapi import APIRouter, HTTPException, Request

from optimade import __api_version__
from optimade.models import (
    ErrorResponse,
    InfoResponse,
    EntryInfoResponse,
)
from optimade.server.routers.utils import meta_values

from aiida_optimade.models import StructureResource
from aiida_optimade.utils import retrieve_queryable_properties


ROUTER = APIRouter(redirect_slashes=True)

ENTRY_INFO_SCHEMAS = {"structures": StructureResource.schema}


@ROUTER.get(
    "/info",
    response_model=Union[InfoResponse, ErrorResponse],
    response_model_exclude_unset=True,
    response_model_exclude_none=False,
    tags=["Info"],
)
def get_info(request: Request):
    from optimade.models import BaseInfoResource, BaseInfoAttributes
    from optimade.server.routers.utils import get_base_url

    parse_result = urllib.parse.urlparse(str(request.url))
    base_url = get_base_url(parse_result)

    return InfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=BaseInfoResource(
            id=BaseInfoResource.schema()["properties"]["id"]["const"],
            type=BaseInfoResource.schema()["properties"]["type"]["const"],
            attributes=BaseInfoAttributes(
                api_version=__api_version__,
                available_api_versions=[
                    {
                        "url": f"{base_url}/v{__api_version__.split('-')[0].split('+')[0].split('.')[0]}",
                        "version": __api_version__,
                    }
                ],
                formats=["json"],
                entry_types_by_format={"json": list(ENTRY_INFO_SCHEMAS.keys())},
                available_endpoints=[
                    "info",
                    "links",
                    "extensions/docs",
                    "extensions/redoc",
                    "extensions/openapi.json",
                ]
                + list(ENTRY_INFO_SCHEMAS.keys()),
                is_index=False,
            ),
        ),
    )


@ROUTER.get(
    "/info/{entry}",
    response_model=Union[EntryInfoResponse, ErrorResponse],
    response_model_exclude_unset=True,
    response_model_exclude_none=False,
    tags=["Info"],
)
def get_info_entry(request: Request, entry: str):
    from optimade.models import EntryInfoResource

    valid_entry_info_endpoints = ENTRY_INFO_SCHEMAS.keys()
    if entry not in valid_entry_info_endpoints:
        raise HTTPException(
            status_code=404,
            detail=f"Entry info not found for {entry}, valid entry info endpoints are:"
            f" {valid_entry_info_endpoints}",
        )

    schema = ENTRY_INFO_SCHEMAS[entry]()
    queryable_properties = {"id", "type", "attributes"}
    properties, _ = retrieve_queryable_properties(schema, queryable_properties)

    output_fields_by_format = {"json": list(properties.keys())}

    return EntryInfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=EntryInfoResource(
            formats=list(output_fields_by_format.keys()),
            description=schema.get(
                "description",
                "Endpoint to represent AiiDA Nodes in the OPTIMADE format",
            ),
            properties=properties,
            output_fields_by_format=output_fields_by_format,
        ),
    )
