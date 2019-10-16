from pydantic import Schema, BaseModel
from typing import Union, Dict

from .links import ChildResource
from .baseinfo import BaseInfoAttributes, BaseInfoResource


class IndexInfoAttributes(BaseInfoAttributes):
    """Attributes for Base URL Info endpoint for an Index Meta-Database"""

    is_index: bool
    is_index.default = True
    is_index.const = True


class RelatedChildResource(ChildResource):
    """Keep only type and id of a ChildResource"""

    if attributes:
        del attributes


class IndexRelationship(BaseModel):
    """Index Meta-Database relationship"""

    data: Union[None, RelatedChildResource] = Schema(
        ...,
        description="JSON API resource linkage. It MUST be either null or contain "
        "a single child identifier object with the fields:",
    )


class IndexInfoResource(BaseInfoResource):
    """Index Meta-Database Base URL Info enpoint resource"""

    attributes: IndexInfoAttributes
    relationships: Dict[str, IndexRelationship] = Schema(
        ...,
        description="Reference to the child identifier object under the links endpoint "
        "that the provider has chosen as their 'default' OPTiMaDe API database. "
        "A client SHOULD present this database as the first choice when an end-user "
        "chooses this provider.",
    )
