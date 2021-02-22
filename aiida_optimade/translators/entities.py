from typing import Any, List, Union
from aiida.orm.nodes import Node
from aiida.orm.querybuilder import QueryBuilder

from aiida_optimade.common import AiidaEntityNotFound, AiidaError, LOGGER


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

    def store_attributes(self, mongo: bool = False) -> None:
        """Store new attributes and reset self._node

        By default, store the attributes as a Node extra.

        Parameters:
            mongo: Store in a MongoDB collection instead of in Node extras.

        """
        if self.new_attributes:
            if mongo:
                self._store_attributes_mongo()
            else:
                self._store_attributes_node_extra()

        # Lastly, reset _node, which will also del __node to remove it from memory
        self._node = None

    def _store_attributes_mongo(self) -> None:
        """Store new attributes in MongoDB collection"""
        import bson.json_util
        from aiida_optimade.routers.structures import STRUCTURES_MONGO
        from aiida_optimade.translators.utils import hex_to_floats

        optimade = STRUCTURES_MONGO.collection.find_one(filter={"id": self._pk})
        if optimade:
            optimade.update(self.new_attributes)
        else:
            optimade = self.new_attributes

        # Don't save float as hex values
        float_fields = {
            "elements_ratios",
            "lattice_vectors",
            "cartesian_site_positions",
        }
        for field in float_fields:
            if optimade.get(field) is not None:
                optimade[field] = hex_to_floats(optimade[field])

        # Add AiiDA Node-specific fields
        optimade.update({"id": str(self._pk)})
        if self._node_loaded:
            optimade.update(
                {
                    "immutable_id": self._node.uuid,
                    "last_modified": self._node.mtime,
                    "ctime": self._node.ctime,
                }
            )
        else:
            field_mapping = {
                "uuid": "immutable_id",
                "mtime": "last_modified",
                "ctime": "ctime",
            }
            optimade.update(
                {
                    field_mapping[field]: value
                    for field, value in zip(
                        field_mapping.keys(),
                        self._get_unique_node_property(list(field_mapping.keys())),
                    )
                }
            )

        LOGGER.debug(
            "(%s) Upserting Node %s in MongoDB!",
            STRUCTURES_MONGO.collection.full_name,
            self._pk,
        )
        STRUCTURES_MONGO.collection.replace_one(
            filter={"id": self._pk},
            replacement=bson.json_util.loads(bson.json_util.dumps(optimade)),
            upsert=True,
        )

    def _store_attributes_node_extra(self) -> None:
        """Store new attributes in Node extras"""
        from aiida.manage.manager import get_manager

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
        LOGGER.debug(
            "(%s) Updating Node %s in AiiDA DB!", profile.database_backend, self._pk
        )
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
