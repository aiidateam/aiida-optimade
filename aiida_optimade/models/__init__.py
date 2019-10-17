from .jsonapi import Link, Resource
from .structures import StructureResource, StructureMapper
from .entries import (
    EntryInfoAttributes,
    EntryPropertyInfo,
    EntryInfoResource,
    ResourceMapper,
)
from .baseinfo import BaseInfoResource, BaseInfoAttributes
from .toplevel import (
    ResponseMeta,
    ResponseMetaQuery,
    StructureResponseMany,
    InfoResponse,
    Provider,
    EntryInfoResponse,
)
from .util import NonnegativeInt
