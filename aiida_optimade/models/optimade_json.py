"""Modified JSON API for OPTiMaDe API"""
from pydantic import Schema, validator
from typing import Optional, Set
from . import jsonapi


class Error(jsonapi.Error):
    """detail MUST be present"""

    detail: str = Schema(
        ...,
        description="A human-readable explanation specific to this occurrence of the problem.",
    )


class Failure(jsonapi.Response):
    """errors MUST be present and data MUST be skipped"""

    meta: Optional[jsonapi.Meta] = Schema(
        ...,
        description="A meta object containing non-standard information related to the Success",
    )
    errors: Set[Error] = Schema(
        ...,
        description="A list of JSON API error objects, where the field detail MUST be present.",
    )
    links: Optional[jsonapi.ToplevelLinks] = Schema(
        ..., description="Links associated with the primary data"
    )

    @validator("data")
    def data_must_be_skipped(cls, value):
        raise AssertionError("data MUST be skipped for failures reporting errors")


class Success(jsonapi.Response):
    """errors are not allowed"""

    meta: Optional[jsonapi.Meta] = Schema(
        ...,
        description="A meta object containing non-standard information related to the Success",
    )
    links: Optional[jsonapi.ToplevelLinks] = Schema(
        ..., description="Links associated with the primary data"
    )

    @validator("meta", always=True)
    def either_data_or_meta_must_be_set(cls, value, values):
        if values.get("data", None) is None and value is None:
            raise AssertionError("Either 'data' or 'meta' must be specified")
        return value

    @validator("errors")
    def either_data_meta_or_errors_must_be_set(cls, value, values):
        raise AssertionError("'errors' MUST be skipped for a successful response")


class Warnings(Error):
    """Warning object, similar to Error objects, but without error codes ('status')

    Note: Must be named "Warnings", since "Warning" is a built-in Python class.
    """

    type: str = Schema(
        "warning", const=True, description='Warnings must of type "warning"'
    )

    @validator("status")
    def status_must_not_be_specified(cls, value):
        raise AssertionError("status MUST NOT be specified for warnings")
