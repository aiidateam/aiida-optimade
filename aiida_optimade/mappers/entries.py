import abc
from aiida_optimade.transformers.aiida import op_conv_map


__all__ = ("ResourceMapper",)


class ResourceMapper(metaclass=abc.ABCMeta):
    """Generic Resource Mapper"""

    ALIASES = ()
    PROJECT_PREFIX = "extras.optimade."

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
        return f"{cls.PROJECT_PREFIX}{real}"

    @abc.abstractclassmethod
    def map_back(self, entity_properties: dict) -> dict:
        """Map properties from AiiDA to OPTiMaDe

        :return: A resource object in OPTiMaDe format
        :rtype: dict
        """

    @abc.abstractclassmethod
    def build_attributes(cls, retrieved_attributes: dict) -> dict:
        """Build attributes dictionary for OPTiMaDe structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict
        """
