from typing import Union, Any
from aiida.orm import Node, QueryBuilder

from aiida_optimade.common import AiidaEntityNotFound


__all__ = ("AiidaEntityParser",)


class AiidaEntityParser:
    """Create OPTiMaDe entry attributes from an AiiDA Entity Node - Base class

    For speed and reusability, save attributes in the Node's extras.
    Each OPTiMaDe attribute should be a method in subclasses of this class.
    """

    EXTRAS_KEY = "optimade"
    AIIDA_ENTITY = Node  # This should be the front-end AiiDA Node class

    def __init__(self, uuid: str):
        self._uuid = uuid
        self.new_attributes = {}
        self.__node = None

    def _get_unique_node_property(self, project: str) -> Union[Node, Any]:
        query = QueryBuilder(limit=1)
        query.append(self.AIIDA_ENTITY, filters={"uuid": self._uuid}, project=project)
        if query.count() != 1:
            raise AiidaEntityNotFound(
                f"Could not find {self.AIIDA_ENTITY} with UUID {self._uuid}."
            )
        return query.first()[0]

    @property
    def _node(self) -> Node:
        if not self._node_loaded:
            self.__node = self._get_unique_node_property("*")
        elif getattr(self.__node, "uuid", "") != self._uuid:
            self.__node = self._get_unique_node_property("*")
        return self.__node

    @_node.setter
    def _node(self, value: Union[None, Node]):
        self.__node = value

    def _node_loaded(self):
        return bool(self.__node)

    def _get_optimade_extras(self) -> Union[None, dict]:
        if self._node_loaded:
            return self._node.extras.get(self.EXTRAS_KEY, None)
        return self._get_unique_node_property(f"extras.{self.EXTRAS_KEY}")

    def store_attributes(self):
        """Store new attributes in Node extras and reset self._node"""
        if self.new_attributes:
            optimade = self._get_optimade_extras()
            if optimade:
                optimade.update(self.new_attributes)
            else:
                optimade = self.new_attributes

            self._node.set_extra(self.EXTRAS_KEY, optimade)

        # Lastly, reset NODE in an attempt to remove it from memory
        self._node = None
