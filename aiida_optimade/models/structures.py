# pylint: disable=missing-class-docstring,too-few-public-methods
from datetime import datetime

from optimade.models import StructureResource as OptimadeStructureResource
from optimade.models import (
    StructureResourceAttributes as OptimadeStructureResourceAttributes,
)
from pydantic import Field


def prefix_provider(string: str) -> str:
    """Prefix string with `_{provider}_`"""
    from optimade.server.config import CONFIG

    if string in CONFIG.provider_fields.get("structures", []):
        return f"_{CONFIG.provider.prefix}_{string}"
    return string


class StructureResourceAttributes(OptimadeStructureResourceAttributes):
    """Extended StructureResourceAttributes for AiiDA-specific fields"""

    ctime: datetime = Field(
        ..., description="Creation time of the Node in the AiiDA database."
    )

    class Config:
        alias_generator = prefix_provider


class StructureResource(OptimadeStructureResource):
    """Extended StructureResourceAttributes for AiiDA-specific fields"""

    attributes: StructureResourceAttributes
