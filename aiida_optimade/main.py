import urllib
import json
from typing import Union
import os

from pydantic import ValidationError
from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from aiida import orm, load_profile

from optimade.server.deps import EntryListingQueryParams, SingleEntryQueryParams
from optimade.models import (
    ToplevelLinks,
    StructureResource,
    InfoResponse,
    EntryInfoResponse,
    ErrorResponse,
    StructureResponseMany,
    StructureResponseOne,
)

from aiida_optimade.entry_collections import AiidaCollection
from aiida_optimade.common.exceptions import AiidaError
from aiida_optimade.config import CONFIG
from aiida_optimade.mappers import StructureMapper
import aiida_optimade.utils as u


app = FastAPI(
    title="OPTiMaDe API for AiiDA",
    description=(
        """The [Open Databases Integration for Materials Design (OPTiMaDe) consortium](http://www.optimade.org/) aims to make materials databases interoperational by developing a common REST API.

[Automated Interactive Infrastructure and Database for Computational Science (AiiDA)](http://www.aiida.net) aims to help researchers with managing complex workflows and making them fully reproducible."""
    ),
    version="0.10.0",
)

profile_name = os.getenv("AIIDA_PROFILE", None)
profile = load_profile(profile_name)

structures = AiidaCollection(
    orm.StructureData.objects, StructureResource, StructureMapper
)


@app.middleware("http")
async def backend_middleware(request: Request, call_next):
    response = None
    try:
        if profile.database_backend == "django":
            from aiida_optimade.aiida_session import (
                OptimadeDjangoBackend as OptimadeBackend,
            )
        elif profile.database_backend == "sqlalchemy":
            from aiida_optimade.aiida_session import (
                OptimadeSqlaBackend as OptimadeBackend,
            )
        else:
            raise AiidaError(
                f'Unknown AiiDA backend "{profile.database_backend}" for profile {profile}'
            )

        request.state.backend = OptimadeBackend()
        response = await call_next(request)
    finally:
        request.state.backend.close()

    if response:
        return response
    raise AiidaError("Failed to properly handle AiiDA backend middleware")


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return u.general_exception(request, exc)


@app.exception_handler(RequestValidationError)
def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return u.general_exception(request, exc)


@app.exception_handler(ValidationError)
def validation_exception_handler(request: Request, exc: ValidationError):
    from optimade.models import Error, ErrorSource

    status = 500
    title = "ValidationError"
    errors = []
    for error in exc.errors():
        pointer = "/" + "/".join([str(_) for _ in error["loc"]])
        source = ErrorSource(pointer=pointer)
        code = error["type"]
        detail = error["msg"]
        errors.append(
            Error(detail=detail, status=status, title=title, source=source, code=code)
        )
    return u.general_exception(request, exc, status_code=status, errors=errors)


@app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    return u.general_exception(request, exc)


@app.get(
    "/structures",
    response_model=Union[StructureResponseMany, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_structures(
    request: Request,
    params: EntryListingQueryParams = Depends(),
    backend: orm.implementation.Backend = Depends(u.get_backend),
):
    results, more_data_available, data_available, fields = structures.find(
        backend, params
    )
    parse_result = urllib.parse.urlparse(str(request.url))

    pagination = {}
    query = urllib.parse.parse_qs(parse_result.query)
    query["page_offset"] = int(query.get("page_offset", ["0"])[0]) - int(
        query.get("page_limit", [CONFIG.page_limit])[0]
    )
    if query["page_offset"] > 0:
        urlencoded_prev = urllib.parse.urlencode(query, doseq=True)
        pagination[
            "prev"
        ] = f"{parse_result.scheme}://{parse_result.netloc}{parse_result.path}?{urlencoded_prev}"
    elif query["page_offset"] == 0 or abs(query["page_offset"]) < int(
        query.get("page_limit", [CONFIG.page_limit])[0]
    ):
        prev_query = query.copy()
        prev_query.pop("page_offset")
        urlencoded_prev = urllib.parse.urlencode(prev_query, doseq=True)
        pagination[
            "prev"
        ] = f"{parse_result.scheme}://{parse_result.netloc}{parse_result.path}?{urlencoded_prev}"

    if more_data_available:
        query["page_offset"] = (
            int(query.get("page_offset", 0))
            + len(results)
            + int(query.get("page_limit", [CONFIG.page_limit])[0])
        )
        urlencoded_next = urllib.parse.urlencode(query, doseq=True)
        pagination[
            "next"
        ] = f"{parse_result.scheme}://{parse_result.netloc}{parse_result.path}?{urlencoded_next}"
    else:
        pagination["next"] = None

    if fields:
        results = u.handle_response_fields(results, fields)

    return StructureResponseMany(
        links=ToplevelLinks(**pagination),
        data=results,
        meta=u.meta_values(
            str(request.url), len(results), data_available, more_data_available
        ),
    )


@app.get(
    "/structures/{entry_id}",
    response_model=Union[StructureResponseOne, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_single_structure(
    request: Request,
    entry_id: int,
    params: SingleEntryQueryParams = Depends(),
    backend: orm.implementation.Backend = Depends(u.get_backend),
):
    params.filter = f"id={entry_id}"
    results, more_data_available, data_available, fields = structures.find(
        backend, params
    )

    if more_data_available:
        raise StarletteHTTPException(
            status_code=500,
            detail=f"more_data_available MUST be False for single entry response, however it is {more_data_available}",
        )
    links = ToplevelLinks(next=None)

    if fields and results is not None:
        results = u.handle_response_fields(results, fields)[0]

    data_returned = 1 if results else 0

    return StructureResponseOne(
        links=links,
        data=results,
        meta=u.meta_values(
            str(request.url), data_returned, data_available, more_data_available
        ),
    )


@app.get(
    "/info",
    response_model=Union[InfoResponse, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Info"],
)
def get_info(request: Request):
    from optimade.models import BaseInfoResource, BaseInfoAttributes

    parse_result = urllib.parse.urlparse(str(request.url))
    return InfoResponse(
        meta=u.meta_values(str(request.url), 1, 1, more_data_available=False),
        data=BaseInfoResource(
            attributes=BaseInfoAttributes(
                api_version="v0.10",
                available_api_versions=[
                    {
                        "url": f"{parse_result.scheme}://{parse_result.netloc}",
                        "version": "0.10.0",
                    }
                ],
                entry_types_by_format={"json": ["structures"]},
                available_endpoints=["info", "structures"],
            )
        ),
    )


@app.get(
    "/info/structures",
    response_model=Union[EntryInfoResponse, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure", "Info"],
)
def get_info_structures(request: Request):
    from optimade.models import EntryInfoResource

    schema = StructureResource.schema()
    queryable_properties = {"id", "type", "attributes"}
    properties = u.retrieve_queryable_properties(schema, queryable_properties)
    for field, field_info in tuple(properties.items()):
        for field_info_name in list(field_info.keys()):
            if field_info_name not in {"description", "unit", "sortable"}:
                del properties[field][field_info_name]

    output_fields_by_format = {"json": list(properties.keys())}

    return EntryInfoResponse(
        meta=u.meta_values(str(request.url), 1, 1, more_data_available=False),
        data=EntryInfoResource(
            formats=list(output_fields_by_format.keys()),
            description="Endpoint to represent AiiDA StructureData Nodes in the OPTiMaDe format",
            properties=properties,
            output_fields_by_format=output_fields_by_format,
        ),
    )


def update_schema(app):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    with open("local_openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)


@app.on_event("startup")
async def startup_event():
    update_schema(app)
