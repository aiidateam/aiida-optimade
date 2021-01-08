from typing import Union

from aiida.orm import CifData, StructureData

from aiida_optimade.translators.structures import StructureDataTranslator


__all__ = ("CifDataTranslator",)


class CifDataTranslator(StructureDataTranslator):
    """Create OPTIMADE "structures" attributes from an AiiDA CifData Node

    Each OPTIMADE field is a method in this or the parent class.
    The approach here is to use CifData's `get_structure()` method to transform the
    CifData into an un-stored in-memory StructureData node.
    From this the `StructureDataTranslator` class may then be used to calculate all
    fields.
    Afterwards, the temporary StructureData node will be cleared from memory and all
    fields stored in the CifData node's `extras`.

    NOTE: Unlike the parent class, this class is a short-term solution and will load
    each CifData Node to utilize the `get_structure()` method.
    """

    AIIDA_ENTITY = CifData

    def __init__(self, pk: str):
        super().__init__(pk)

        self.__kinds = None
        self.__sites = None
        self.__pbc = None
        self.__cell = None

    @property
    def _node(self) -> StructureData:
        if not self._node_loaded:
            self.__node = self._get_unique_node_property("*")
        elif getattr(self.__node, "pk", 0) != self._pk:
            self.__node = self._get_unique_node_property("*")
        if isinstance(self.__node, StructureData):
            return self.__node
        extras = self.__node.extras.copy()
        self.__node: StructureData = self.__node.get_structure(
            converter="pymatgen",
            store=False,
            primitive_cell=False,
        )
        self.__node.set_extra_many(extras)
        return self.__node

    @_node.setter
    def _node(self, value: Union[None, CifData, StructureData]):
        if self._node_loaded:
            del self.__node
        self.__node = value

    @property
    def _kinds(self) -> list:
        if not self.__kinds or self.__kinds is None:
            self.__kinds = [_.get_raw() for _ in self._node.kinds]
        return self.__kinds

    @property
    def _sites(self) -> list:
        if not self.__sites or self.__sites is None:
            self.__sites = [_.get_raw() for _ in self._node.sites]
        return self.__sites

    @property
    def _pbc(self) -> list:
        if not self.__pbc:
            self.__pbc = [int(_) for _ in self._node.pbc]
        return self.__pbc

    @property
    def _cell(self) -> list:
        if not self.__cell:
            self.__cell = self._node.cell.copy()
        return self.__cell
