import urllib
import json
import traceback
from datetime import datetime
from typing import Union, Dict, Any, List, Sequence

from pydantic import ValidationError
from fastapi import FastAPI, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from aiida import orm, load_profile

from optimade.server.deps import EntryListingQueryParams, SingleEntryQueryParams
from optimade.models import (
    ToplevelLinks,
    StructureResource,
    EntryInfoResource,
    BaseInfoResource,
    BaseInfoAttributes,
    ResponseMeta,
    ResponseMetaQuery,
    StructureResponseMany,
    InfoResponse,
    Provider,
    Failure,
    EntryInfoResponse,
    Error,
    ErrorResponse,
    ErrorSource,
    EntryResource,
    StructureResponseOne,
)

from aiida_optimade.entry_collections import AiidaCollection
from aiida_optimade.common.exceptions import AiidaError
from aiida_optimade.config import CONFIG
from aiida_optimade.mappers import StructureMapper


app = FastAPI(
    title="OPTiMaDe API for AiiDA",
    description=(
        """The [Open Databases Integration for Materials Design (OPTiMaDe) consortium](http://www.optimade.org/) aims to make materials databases interoperational by developing a common REST API.

[Automated Interactive Infrastructure and Database for Computational Science (AiiDA)](http://www.aiida.net) aims to help researchers with managing complex workflows and making them fully reproducible."""
    ),
    version="0.10.0",
)

profile = load_profile("sohier_import_sqla")

structures = AiidaCollection(
    orm.StructureData.objects, StructureResource, StructureMapper
)


def meta_values(
    url, data_returned, data_available, more_data_available=False, **kwargs
):
    """Helper to initialize the meta values"""
    parse_result = urllib.parse.urlparse(url)
    provider = CONFIG.provider.copy()
    provider["prefix"] = provider["prefix"][1:-1]  # Remove surrounding `_`
    return ResponseMeta(
        query=ResponseMetaQuery(
            representation=f"{parse_result.path}?{parse_result.query}"
        ),
        api_version="v0.10",
        time_stamp=datetime.utcnow(),
        data_returned=data_returned,
        more_data_available=more_data_available,
        provider=Provider(**provider),
        data_available=data_available,
        **kwargs,
    )


def update_schema(app):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    with open("local_openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)


def general_exception(
    request: Request, exc: Exception, **kwargs: Dict[str, Any]
) -> JSONResponse:
    tb = "".join(
        traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
    )
    print(tb)

    try:
        status_code = exc.status_code
    except AttributeError:
        status_code = kwargs.get("status_code", 500)

    detail = getattr(exc, "detail", str(exc))

    errors = kwargs.get("errors", None)
    if not errors:
        errors = [
            Error(detail=detail, status=status_code, title=str(exc.__class__.__name__))
        ]

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            ErrorResponse(
                meta=meta_values(
                    # TODO: Add debug and print only tb if debug = True
                    str(request.url),
                    0,
                    0,
                    False,
                    **{CONFIG.provider["prefix"] + "traceback": tb},
                ),
                errors=errors,
            ),
            skip_defaults=True,
        ),
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


def get_backend(request: Request):
    return request.state.backend


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return general_exception(request, exc)


@app.exception_handler(RequestValidationError)
def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return general_exception(request, exc)


@app.exception_handler(ValidationError)
def validation_exception_handler(request: Request, exc: ValidationError):
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
    return general_exception(request, exc, status_code=status, errors=errors)


@app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    return general_exception(request, exc)


def handle_response_fields(
    results: Union[List[EntryResource], EntryResource], fields: set
) -> dict:
    if not isinstance(results, list):
        results = [results]
    non_attribute_fields = {"id", "type"}
    top_level = {_ for _ in non_attribute_fields if _ in fields}
    attribute_level = fields - non_attribute_fields
    new_results = []
    while results:
        entry = results.pop(0)
        new_entry = entry.dict(exclude=top_level, skip_defaults=True)
        for field in attribute_level:
            if field in new_entry["attributes"]:
                del new_entry["attributes"][field]
        if not new_entry["attributes"]:
            del new_entry["attributes"]
        new_results.append(new_entry)
    return new_results


@app.get(
    "/structures",
    response_model=Union[StructureResponseMany, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_structures(
    request: Request,
    params: EntryListingQueryParams = Depends(),
    backend: orm.implementation.Backend = Depends(get_backend),
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
        results = handle_response_fields(results, fields)

    return StructureResponseMany(
        links=ToplevelLinks(**pagination),
        data=results,
        meta=meta_values(
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
    backend: orm.implementation.Backend = Depends(get_backend),
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
        results = handle_response_fields(results, fields)[0]

    data_returned = 1 if results else 0

    return StructureResponseOne(
        links=links,
        data=results,
        meta=meta_values(
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
    parse_result = urllib.parse.urlparse(str(request.url))
    return InfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
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


def retrieve_queryable_properties(schema: dict, queryable_properties: Sequence):
    properties = {}
    for name, value in schema["properties"].items():
        if name in queryable_properties:
            if "$ref" in value:
                path = value["$ref"].split("/")[1:]
                sub_schema = schema.copy()
                while path:
                    next_key = path.pop(0)
                    sub_schema = sub_schema[next_key]
                sub_queryable_properties = sub_schema["properties"].keys()
                properties.update(
                    retrieve_queryable_properties(sub_schema, sub_queryable_properties)
                )
            else:
                properties[name] = {"description": value["description"]}
                if "unit" in value:
                    properties[name]["unit"] = value["unit"]
    return properties


@app.get(
    "/info/structures",
    response_model=Union[EntryInfoResponse, Failure],
    response_model_skip_defaults=True,
    tags=["Structure", "Info"],
)
def get_info_structures(request: Request):
    schema = StructureResource.schema()
    queryable_properties = {"id", "type", "attributes"}
    properties = retrieve_queryable_properties(schema, queryable_properties)

    output_fields_by_format = {"json": list(properties.keys())}

    return EntryInfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=EntryInfoResource(
            formats=list(output_fields_by_format.keys()),
            description="Endpoint to represent AiiDA StructureData Nodes in the OPTiMaDe format",
            properties=properties,
            output_fields_by_format=output_fields_by_format,
        ),
    )


@app.on_event("startup")
async def startup_event():
    update_schema(app)
