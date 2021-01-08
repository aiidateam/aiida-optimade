from typing import Any, List, Union
from aiida.orm import Node, QueryBuilder
from aiida.manage.manager import get_manager

from aiida_optimade.common import AiidaEntityNotFound, AiidaError


__all__ = ("AiidaEntityTranslator",)


class AiidaEntityTranslator:  # pylint: disable=too-few-public-methods
    """Create OPTIMADE entry attributes from an AiiDA Entity Node - Base class

    For speed and reusability, save attributes in the Node's extras.
    Each OPTIMADE attribute should be a method in subclasses of this class.
    """

    EXTRAS_KEY = "optimade"
    AIIDA_ENTITY = Node  # This should be the front-end AiiDA Node class

    def __init__(self, pk: int):
        self._pk = pk
        self.new_attributes = {}
        self.__node = None

    def _get_unique_node_property(
        self, project: Union[List[str], str]
    ) -> Union[Node, Any]:
        query = QueryBuilder(limit=1)
        query.append(self.AIIDA_ENTITY, filters={"id": self._pk}, project=project)
        if query.count() != 1:
            raise AiidaEntityNotFound(
                f"Could not find {self.AIIDA_ENTITY} with PK {self._pk}."
            )
        res = query.first()
        del query
        return res if len(res) > 1 else res[0]

    @property
    def _node(self) -> Node:
        if not self._node_loaded:
            self.__node = self._get_unique_node_property("*")
        elif getattr(self.__node, "pk", 0) != self._pk:
            self.__node = self._get_unique_node_property("*")
        return self.__node

    @_node.setter
    def _node(self, value: Union[None, Node]):
        if self._node_loaded:
            del self.__node
        self.__node = value

    @property
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
            extras = (
                self._get_unique_node_property("extras")
                if self._get_unique_node_property("extras")
                else {}
            )
            extras[self.EXTRAS_KEY] = optimade

            profile = get_manager().get_profile()
            if profile.database_backend == "django":
                from aiida.backends.djsite.db.models import DbNode

                with get_manager().get_backend().transaction():
                    DbNode.objects.filter(pk=self._pk).update(extras=extras)
            elif profile.database_backend == "sqlalchemy":
                from aiida.backends.sqlalchemy.models.node import DbNode

                with get_manager().get_backend().transaction() as session:
                    session.query(DbNode).filter(DbNode.id == self._pk).update(
                        values={"extras": extras}
                    )
            else:
                raise AiidaError(
                    f'Unknown AiiDA backend "{profile.database_backend}" for profile'
                    f"{profile}"
                )

            # For posterity, this is how to do the same, going through AiiDA's API:
            # self._node.set_extra(self.EXTRAS_KEY, optimade)

        # Lastly, reset _node and del __node in an attempt to remove it from memory
        self._node = None
