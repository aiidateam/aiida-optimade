import abc
from typing import Tuple
from aiida_optimade.transformers.aiida import op_conv_map
from aiida_optimade.config import CONFIG

from aiida_optimade.parsers.entities import AiidaEntityParser


__all__ = ("ResourceMapper",)


class ResourceMapper(metaclass=abc.ABCMeta):
    """Generic Resource Mapper"""

    ENDPOINT: str = ""
    ALIASES: tuple = ()
    PROJECT_PREFIX: str = "extras.optimade."
    PARSER: AiidaEntityParser = AiidaEntityParser
    ALL_ATTRIBUTES: list = []
    REQUIRED_ATTRIBUTES: list = []

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        return (
            tuple(
                (CONFIG.provider["prefix"] + field, field)
                for field in CONFIG.provider_fields[cls.ENDPOINT]
            )
            + cls.ALIASES
        )

    @classmethod
    def alias_for(cls, field):
        """Return aliased field name

        :return: Aliased field as found in cls.ALIASES
        :rtype: str
        """
        real = dict(cls.ALIASES).get(field, field)
        no_prefix = {"id"}
        no_prefix = no_prefix.union(set(op_conv_map.values()))
        if real != field or (real == field and real in no_prefix):
            return real
        if real == field and real.startswith(CONFIG.provider["prefix"]):
            return real[len(CONFIG.provider["prefix"]) :]
        return f"{cls.PROJECT_PREFIX}{real}"

    @abc.abstractclassmethod
    def map_back(self, entity_properties: dict) -> dict:
        """Map properties from AiiDA to OPTiMaDe

        :return: A resource object in OPTiMaDe format
        :rtype: dict
        """

    @abc.abstractclassmethod
    def build_attributes(cls, retrieved_attributes: dict, entry_pk: int) -> dict:
        """Build attributes dictionary for OPTiMaDe structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict

        :param entry_pk: The AiiDA Node's PK
        :type entry_pk: int
        """
