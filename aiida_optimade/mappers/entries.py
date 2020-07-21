# pylint: disable=arguments-differ
from typing import Tuple

from optimade.server.mappers import BaseResourceMapper as OptimadeResourceMapper

from aiida_optimade.translators.entities import AiidaEntityTranslator


__all__ = ("ResourceMapper",)


class ResourceMapper(OptimadeResourceMapper):
    """Generic Resource Mapper"""

    PROJECT_PREFIX: str = "extras.optimade."

    TRANSLATOR: AiidaEntityTranslator = AiidaEntityTranslator
    ALL_ATTRIBUTES: set = set()
    REQUIRED_ATTRIBUTES: set = set()

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        """Get all aliases as a tuple
        Also add `PROJECT_PREFIX` fields to the tuple
        """
        res = super(ResourceMapper, cls).all_aliases()
        return res + tuple(
            (field, f"{cls.PROJECT_PREFIX}{field}")
            for field in cls.ALL_ATTRIBUTES
            if field not in dict(res)
        )

    @classmethod
    def map_back(cls, entity_properties: dict) -> dict:
        """Map properties from AiiDA to OPTIMADE

        :param entity_properties: Found AiiDA properties through QueryBuilder query
        :type entity_properties: dict

        :return: A resource object in OPTIMADE format
        :rtype: dict
        """
        mapping = ((real, alias) for alias, real in cls.all_aliases())

        new_object_attributes = {}
        new_object = {}

        for real, alias in mapping:
            if (
                real in entity_properties
                and entity_properties[real] is not None
                and alias not in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS
            ):
                new_object_attributes[alias] = entity_properties[real]

        # We always need "id"
        if "id" not in entity_properties:
            raise KeyError(
                f'"id" should be present in entity_properties: {entity_properties}'
            )

        for field in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS:
            value = entity_properties.get(field, None)
            if value is not None:
                new_object[field] = value

        new_object["attributes"] = cls.build_attributes(
            new_object_attributes, new_object["id"]
        )
        new_object["type"] = cls.ENDPOINT

        return new_object

    @classmethod
    def build_attributes(cls, retrieved_attributes: dict, entry_pk: int) -> dict:
        """Build attributes dictionary for OPTIMADE structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict

        :param entry_pk: The AiiDA Node's PK
        :type entry_pk: int
        """
