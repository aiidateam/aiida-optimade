from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel, Schema

from .optimade_json import Resource
from .jsonapi import Relationships, Attributes


class EntryResourceAttributes(Attributes):
    """Contains key-value pairs representing the entry's properties"""

    immutable_id: Optional[str] = Schema(
        ...,
        description="an optional field containing the entry's immutable ID "
        "(e.g. a UUID). This is important for databases having "
        "preferred IDs that point to 'the latest version' of a "
        "record, but still offer access to older variants. This ID "
        "maps to the version-specific record, in case it changes "
        "in the future.",
    )

    last_modified: datetime = Schema(
        ...,
        description="an [ISO 8601](https://www.iso.org/standard/40874.html) "
        "representing the entry's last modification time.",
    )


class EntryResource(Resource):

    id.description = (
        "a string which together with the type uniquely identifies "
        "the object and strictly follows the requirements as "
        "specified by `id`. This can be the local database ID."
    )

    type.description = "field containing the type of the entry"

    attributes: EntryResourceAttributes = Schema(
        ...,
        description="a dictionary containing key-value pairs representing the "
        "entry's properties.",
    )

    relationships: Optional[Relationships] = Schema(
        ...,
        description="a dictionary containing references to other resource "
        "objects as defined by the JSON API relationships object.",
    )


class EntryPropertyInfo(BaseModel):

    description: str = Schema(..., description="description of the entry")

    unit: Optional[str] = Schema(..., description="the physical unit of the entry")


class EntryInfoAttributes(BaseModel):

    formats: List[str] = Schema(
        ["jsonapi"], description="list of available output formats."
    )

    description: str = Schema(..., description="description of the entry")

    properties: Dict[str, EntryPropertyInfo] = Schema(
        ...,
        description="a dictionary describing queryable properties for this "
        "entry type, where each key is a property ID.",
    )

    output_fields_by_format: Dict[str, List[str]] = Schema(
        ...,
        description="a dictionary of available output fields for this entry "
        "type, where the keys are the values of the `formats` list "
        "and the values are the keys of the `properties` dictionary.",
    )


class EntryInfoResource(BaseModel):
    id: str = Schema(..., description="unique ID for this resource object")

    type: str = Schema("info", description="type of this resource")

    attributes: EntryInfoAttributes