from typing import Tuple
import urllib.parse

from optimade.models import DataType
from optimade.server.config import CONFIG


OPEN_API_ENDPOINTS = {
    "docs": "/extensions/docs",
    "redoc": "/extensions/redoc",
    "openapi": "/extensions/openapi.json",
}


def retrieve_queryable_properties(
    schema: dict, queryable_properties: list
) -> Tuple[dict, dict]:
    """Get all queryable properties from an OPTIMADE schema"""
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
                # AiiDA's QueryBuilder can sort everything that isn't a list (array)
                # or dict (object)
                properties[name]["sortable"] = value.get("type", "") not in [
                    "array",
                    "object",
                ]
                # Try to get OpenAPI-specific "format" if possible,
                # else get "type"; a mandatory OpenAPI key.
                properties[name]["type"] = DataType.from_json_type(
                    value.get("format", value["type"])
                )

    return properties, all_properties


def get_custom_base_url_path():
    """Return path part of custom base URL"""
    if CONFIG.base_url is not None:
        res = urllib.parse.urlparse(CONFIG.base_url).path
    else:
        res = urllib.parse.urlparse(CONFIG.base_url).path.decode()

    while res.endswith("/"):
        res = res[:-1]

    return res
