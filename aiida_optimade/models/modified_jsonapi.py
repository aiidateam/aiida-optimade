"""
Modified jsonapi for OptimadeAPI
"""
from datetime import datetime
from pydantic import UrlStr, BaseModel, Schema, validator
from typing import Optional, Union, Set
from . import jsonapi


class Attributes(jsonapi.Attributes):
    """Modification of Attributes to include Optimade specified keys"""

    local_id: UrlStr = Schema(
        ...,
        description="the entry's local database ID (having no OPTiMaDe requirements/conventions",
    )
    last_modified: datetime = Schema(
        ..., description="an ISO 8601 representing the entry's last modification time"
    )
    immutable_id: Optional[UrlStr] = Schema(
        ...,
        description='an OPTIONAL field containing the entry\'s immutable ID (e.g., an UUID). '
        'This is important for databases having preferred IDs that point to "the latest version" of a record, '
        'but still offer access to older variants. This ID maps to the version-specific record, in case it changes in the future.',
    )


class ErrorLinks(BaseModel):
    """Links with recast for Errors"""

    about: Union[jsonapi.Link, UrlStr] = Schema(
        ...,
        description="a link that leads to further details about this particular occurrence of the problem.",
    )


class ResourceLinks(BaseModel):
    """Links with recast for Errors"""

    self: Union[jsonapi.Link, UrlStr] = Schema(
        ..., description="a link that refers to this resource."
    )


class Resource(jsonapi.Resource):
    """Resource objects appear in a JSON:API document to represent resources."""

    links: Optional[ResourceLinks] = Schema(
        ..., description="A links object containing self"
    )


class Error(jsonapi.Error):
    """Error where links uses ErrorLinks"""

    links: Optional[ErrorLinks] = Schema(
        ..., description="A links object containing about"
    )


class Links(jsonapi.Links):
    """Links now store base_url"""

    base_url: Optional[Union[jsonapi.Link, UrlStr]] = Schema(
        ..., description="The URL that serves the API."
    )


class Success(jsonapi.Success):
    """Update with new classes"""

    data: Union[None, Resource, Set[Resource]] = Schema(
        ..., description="Outputted Data"
    )
    included: Optional[Set[Resource]] = Schema(
        ..., description="A list of resources that are included"
    )
    links: Optional[Union[Links, jsonapi.Pagination]] = Schema(
        ..., description="Information about the JSON API used"
    )


class Warnings(Error):
    """Warning object, similar to Error objects, but without error codes ('status')"""

    type: str = Schema(
        'warning',
        const=True,
        description='Warnings must of type "warning"'
    )

    detail: str = Schema(
        ...,
        description="A human-readable explanation specific to this occurrence of the problem."
    )

    @validator("status")
    def status_must_not_be_specified(cls, value):
        if value is not None:
            raise Exception('status MUST NOT be specified')
        return value

