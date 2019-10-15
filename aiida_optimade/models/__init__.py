from .jsonapi import Link
from .modified_jsonapi import Links, Resource
from .structures import StructureResource, StructureMapper
from .entries import EntryInfoAttributes, EntryPropertyInfo, EntryInfoResource
from .baseinfo import BaseInfoResource, BaseInfoAttributes
from .toplevel import (
    ResponseMeta,
    ResponseMetaQuery,
    StructureResponseMany,
    InfoResponse,
    Provider,
    ErrorResponse,
    EntryInfoResponse,
)
from .util import NonnegativeInt
