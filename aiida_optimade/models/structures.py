# pylint: disable=missing-class-docstring,too-few-public-methods
from datetime import datetime
from typing import Optional

from optimade.models import (
    StructureResource as OptimadeStructureResource,
    StructureResourceAttributes as OptimadeStructureResourceAttributes,
)
from optimade.models.utils import OptimadeField, SupportLevel


def prefix_provider(string: str) -> str:
    """Prefix string with `_{provider}_`"""
    from optimade.server.config import CONFIG

    if string in CONFIG.provider_fields.get("structures", []):
        return f"_{CONFIG.provider.prefix}_{string}"
    return string


class StructureResourceAttributes(OptimadeStructureResourceAttributes):
    """Extended StructureResourceAttributes for AiiDA-specific fields"""

    ctime: Optional[datetime] = OptimadeField(
        ...,
        description="Creation time of the Node in the AiiDA database.",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.MUST,
    )

    class Config:
        alias_generator = prefix_provider


class StructureResource(OptimadeStructureResource):
    """Extended StructureResourceAttributes for AiiDA-specific fields"""

    attributes: StructureResourceAttributes
