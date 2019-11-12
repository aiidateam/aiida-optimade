import urllib
import traceback
from datetime import datetime
from typing import Union, Dict, Any, List, Sequence

from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from starlette.responses import JSONResponse

from optimade.models import (
    ResponseMeta,
    ResponseMetaQuery,
    Provider,
    Error,
    ErrorResponse,
    EntryResource,
)

from aiida_optimade.config import CONFIG


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


def get_backend(request: Request):
    return request.state.backend


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
