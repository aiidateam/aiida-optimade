# pylint: disable=arguments-differ
from typing import Any, Dict, Set, Tuple

from optimade.server.mappers import BaseResourceMapper as OptimadeResourceMapper

from aiida_optimade.translators.entities import AiidaEntityTranslator


__all__ = ("ResourceMapper",)


class ResourceMapper(OptimadeResourceMapper):
    """Generic Resource Mapper"""

    PROJECT_PREFIX: str = "extras.optimade."

    TRANSLATORS: Dict[str, AiidaEntityTranslator]
    REQUIRED_ATTRIBUTES: Set[str] = set()
    TOP_LEVEL_NON_ATTRIBUTES_FIELDS: Set[str] = {
        "id",
        "type",
        "relationships",
        "links",
        "meta",
    }

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        """Get all aliases as a tuple
        Also add `PROJECT_PREFIX` fields to the tuple
        """
        res = super(ResourceMapper, cls).all_aliases()
        return res + tuple(
            (field, f"{cls.PROJECT_PREFIX}{field}")
            for field in set(cls.ENTRY_RESOURCE_ATTRIBUTES.keys())
            - cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS
            if field not in dict(res)
        )

    @classmethod
    def map_back(cls, entity_properties: Dict[str, Any]) -> dict:
        """Map properties from AiiDA to OPTIMADE

        Parameters:
            entity_properties: Found AiiDA properties through QueryBuilder query.

        Return:
            A resource object in OPTIMADE format.

        """
        # We always need "id" and "node_type"
        for required_property in ["id", "node_type"]:
            if required_property not in entity_properties:
                raise KeyError(
                    f"{required_property!r} should be present in entity_properties: "
                    f"{entity_properties}"
                )

        new_object = {
            field: entity_properties[cls.get_backend_field(field)]
            for field in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS
            if cls.get_backend_field(field) in entity_properties
        }

        new_object["attributes"] = cls.build_attributes(
            retrieved_attributes={
                alias: entity_properties[real]
                for alias, real in cls.all_aliases()
                if (
                    real in entity_properties
                    and alias not in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS
                )
            },
            entry_pk=new_object["id"],
            node_type=new_object["type"],
        )
        new_object["type"] = cls.ENDPOINT

        return new_object

    @classmethod
    def build_attributes(
        cls,
        retrieved_attributes: dict,
        entry_pk: int,
        node_type: str,
        missing_attributes: dict = None,
    ) -> dict:
        """Build attributes dictionary for OPTIMADE structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict

        :param entry_pk: The AiiDA Node's PK
        :type entry_pk: int

        :param node_type: The AiiDA Node's type
        :type node_type: str
        """
