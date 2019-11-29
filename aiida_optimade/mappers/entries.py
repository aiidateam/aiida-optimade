import abc
from typing import Tuple

from aiida_optimade.config import CONFIG
from aiida_optimade.translators.entities import AiidaEntityTranslator


__all__ = ("ResourceMapper",)


class ResourceMapper(metaclass=abc.ABCMeta):
    """Generic Resource Mapper"""

    PROJECT_PREFIX: str = "extras.optimade."

    ENDPOINT: str = ""
    ALIASES: Tuple[Tuple[str, str]] = ()
    TRANSLATOR: AiidaEntityTranslator = AiidaEntityTranslator
    ALL_ATTRIBUTES: list = []
    REQUIRED_ATTRIBUTES: list = []

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        res = (
            tuple(
                (CONFIG.provider["prefix"] + field, field)
                for field in CONFIG.provider_fields[cls.ENDPOINT]
            )
            + cls.ALIASES
        )
        return res + tuple(
            (field, f"{cls.PROJECT_PREFIX}{field}")
            for field in cls.ALL_ATTRIBUTES
            if field not in dict(res)
        )

    @classmethod
    def alias_for(cls, field):
        """Return aliased field name

        :return: Aliased field as found in cls.ALIASES
        :rtype: str
        """
        return dict(cls.all_aliases()).get(field, field)

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
