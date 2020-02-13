# pylint: disable=arguments-differ
from typing import Tuple

from optimade.server.mappers import ResourceMapper as OptimadeResourceMapper

from aiida_optimade.translators.entities import AiidaEntityTranslator


__all__ = ("ResourceMapper",)


class ResourceMapper(OptimadeResourceMapper):
    """Generic Resource Mapper"""

    PROJECT_PREFIX: str = "extras.optimade."

    TRANSLATOR: AiidaEntityTranslator = AiidaEntityTranslator
    ALL_ATTRIBUTES: list = []
    REQUIRED_ATTRIBUTES: list = []

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        """Get all aliases as a tuple"""
        res = super(ResourceMapper, cls).all_aliases()
        return res + tuple(
            (field, f"{cls.PROJECT_PREFIX}{field}")
            for field in cls.ALL_ATTRIBUTES
            if field not in dict(res)
        )

    @classmethod
    def map_back(cls, entity_properties: dict) -> dict:
        """Map properties from AiiDA to OPTiMaDe

        :param entity_properties: Found AiiDA properties through QueryBuilder query
        :type entity_properties: dict

        :return: A resource object in OPTiMaDe format
        :rtype: dict
        """

    @classmethod
    def build_attributes(cls, retrieved_attributes: dict, entry_pk: int) -> dict:
        """Build attributes dictionary for OPTiMaDe structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict

        :param entry_pk: The AiiDA Node's PK
        :type entry_pk: int
        """
