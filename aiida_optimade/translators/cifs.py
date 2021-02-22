from typing import Union

from aiida.orm.nodes.data.cif import CifData
from aiida.orm.nodes.data.structure import StructureData

from aiida_optimade.translators.structures import StructureDataTranslator


__all__ = ("CifDataTranslator",)


def _get_aiida_structure_pymatgen_inline(cif, **kwargs) -> StructureData:
    """Copy of similar named function in AiiDA-Core.

    Creates :py:class:`aiida.orm.nodes.data.structure.StructureData` using pymatgen.

    :param occupancy_tolerance: If total occupancy of a site is between 1 and
        occupancy_tolerance, the occupancies will be scaled down to 1.
    :param site_tolerance: This tolerance is used to determine if two sites are sitting
        in the same position, in which case they will be combined to a single
        disordered site. Defaults to 1e-4.

    .. note:: requires pymatgen module.

    """
    from aiida.tools.data.cif import InvalidOccupationsError
    from pymatgen.io.cif import CifParser

    parameters = kwargs.get("parameters", {})

    constructor_kwargs = {}

    parameters["primitive"] = parameters.pop("primitive_cell", False)

    for argument in ["occupancy_tolerance", "site_tolerance"]:
        if argument in parameters:
            constructor_kwargs[argument] = parameters.pop(argument)

    with cif.open() as handle:
        parser = CifParser(handle, **constructor_kwargs)

    try:
        structures = parser.get_structures(**parameters)
    except ValueError as exc_one:

        # Verify whether the failure was due to wrong occupancy numbers
        try:
            constructor_kwargs["occupancy_tolerance"] = 1e10
            with cif.open() as handle:
                parser = CifParser(handle, **constructor_kwargs)
            structures = parser.get_structures(**parameters)
        except ValueError as exc_two:
            # If it still fails, the occupancies were not the reason for failure
            raise ValueError(
                "pymatgen failed to provide a structure from the cif file"
            ) from exc_two
        else:
            # If it now succeeds, non-unity occupancies were the culprit
            raise InvalidOccupationsError(
                "detected atomic sites with an occupation number larger than the "
                "occupation tolerance"
            ) from exc_one

    return StructureData(pymatgen_structure=structures[0])


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
        self.__node = _get_aiida_structure_pymatgen_inline(cif=self.__node)
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
