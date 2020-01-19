import urllib
import traceback
from datetime import datetime
from typing import Dict, Any, Tuple

from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from starlette.responses import JSONResponse

from optimade import __api_version__

from optimade.models import (
    ResponseMeta,
    ResponseMetaQuery,
    Provider,
    Implementation,
    Error,
    ErrorResponse,
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
        api_version=f"v{__api_version__}",
        time_stamp=datetime.utcnow(),
        data_returned=data_returned,
        more_data_available=more_data_available,
        provider=Provider(**provider),
        data_available=data_available,
        implementation=Implementation(**CONFIG.implementation),
        **kwargs,
    )


def general_exception(
    request: Request, exc: Exception, **kwargs: Dict[str, Any]
) -> JSONResponse:
    """Helper to return Python exceptions as OPTiMaDe errors in JSON format"""
    trace = "".join(
        traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
    )
    print(trace)

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
                    # TODO: Add debug and print only trace if debug = True
                    str(request.url),
                    0,
                    0,
                    False,
                    **{CONFIG.provider["prefix"] + "traceback": trace},
                ),
                errors=errors,
            ),
            exclude_unset=True,
        ),
    )


def retrieve_queryable_properties(
    schema: dict, queryable_properties: list
) -> Tuple[dict, dict]:
    """Get all queryable properties from an OPTiMaDe schema"""
    properties = {}
    all_properties = {}

    for name, value in schema["properties"].items():
        if name in queryable_properties:
            if "$ref" in value:
                path = value["$ref"].split("/")[1:]
                sub_schema = schema.copy()
                while path:
                    next_key = path.pop(0)
                    sub_schema = sub_schema[next_key]
                sub_queryable_properties = sub_schema["properties"].keys()
                new_properties, new_all_properties = retrieve_queryable_properties(
                    sub_schema, sub_queryable_properties
                )
                properties.update(new_properties)
                all_properties.update(new_all_properties)
            else:
                all_properties[name] = value
                properties[name] = {"description": value.get("description", "")}
                for extra_key in ["unit"]:
                    if extra_key in value:
                        properties[name][extra_key] = value[extra_key]

    return properties, all_properties
