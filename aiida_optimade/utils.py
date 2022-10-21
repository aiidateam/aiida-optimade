from typing import TYPE_CHECKING

from optimade.models import DataType

if TYPE_CHECKING:
    from typing import Any, Dict, Tuple

OPEN_API_ENDPOINTS = {
    "docs": "/extensions/docs",
    "redoc": "/extensions/redoc",
    "openapi": "/extensions/openapi.json",
}


def retrieve_queryable_properties(
    schema: "Dict[str, Dict[str, Any]]", queryable_properties: list
) -> "Tuple[dict, dict]":
    """Get all queryable properties from an OPTIMADE schema"""
    properties = {}
    all_properties = {}

    for name, value in schema.get("properties", {}).items():
        if name in queryable_properties:
            if "$ref" in value:
                path = value.get("$ref", "").split("/")[1:]
                sub_schema = schema.copy()
                while path:
                    next_key = path.pop(0)
                    sub_schema = sub_schema[next_key]
                sub_queryable_properties = sub_schema["properties"].keys()
                new_properties, new_all_properties = retrieve_queryable_properties(
                    sub_schema, list(sub_queryable_properties)
                )
                properties.update(new_properties)
                all_properties.update(new_all_properties)
            else:
                all_properties[name] = value
                properties[name] = {"description": value.get("description", "")}
                for extra_key in (
                    "x-optimade-unit",
                    "x-optimade-queryable",
                    "x-optimade-support",
                ):
                    if value.get(extra_key) is not None:
                        properties[name][extra_key.replace("x-optimade-", "")] = value[
                            extra_key
                        ]
                # AiiDA's QueryBuilder can sort everything that isn't a list (array)
                # or dict (object)
                properties[name]["sortable"] = value.get("type", "") not in [
                    "array",
                    "object",
                ] and value.get("x-optimade-sortable", True)
                # Try to get OpenAPI-specific "format" if possible,
                # else get "type"; a mandatory OpenAPI key.
                properties[name]["type"] = DataType.from_json_type(
                    value.get("format", value["type"])
                )

    return properties, all_properties
