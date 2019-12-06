from aiida.orm import CifData

from .structures import StructureDataTranslator


class CifDataTranslator(StructureDataTranslator):
    """Create OPTIMADE "structures" attributes from an AiiDA CifData Node

    Each OPTIMADE field is a method in this or the parent class.
    The approach here is to use CifData's `get_structure()` method to transform the
        CifData into an un-stored in-memory StructureData node.
    From this the `StructureDataTranslator` class may then be used to calculate all
        fields.
    Afterwards, the temporary StructureData node will be cleared from memory and all
        fields stored in the CifData node's `extras`.

    NOTE: Like the parent class, this class succeeds in *never* loading the actual
        AiiDA Node for optimization purposes.
    """

    AIIDA_ENTITY = CifData
