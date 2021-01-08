from typing import Dict
import warnings

from aiida_optimade.common import NotImplementedWarning
from aiida_optimade.models import StructureResourceAttributes
from aiida_optimade.translators import (
    hex_to_floats,
    AiidaEntityTranslator,
    CifDataTranslator,
    StructureDataTranslator,
)

from .entries import ResourceMapper


__all__ = ("StructureMapper",)


class StructureMapper(ResourceMapper):
    """Map 'structure' resources from OPTIMADE to AiiDA"""

    ENDPOINT = "structures"

    TRANSLATORS: Dict[str, AiidaEntityTranslator] = {
        "data.cif.CifData.": CifDataTranslator,
        "data.structure.StructureData.": StructureDataTranslator,
    }
    ALL_ATTRIBUTES = set(StructureResourceAttributes.schema().get("properties").keys())
    REQUIRED_ATTRIBUTES = set(StructureResourceAttributes.schema().get("required"))
    # This should be REQUIRED_FIELDS, but should be set as such in `optimade`

    @classmethod
    def build_attributes(
        cls, retrieved_attributes: dict, entry_pk: int, node_type: str
    ) -> dict:
        """Build attributes dictionary for OPTIMADE structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict

        :param entry_pk: The AiiDA Node's PK
        :type entry_pk: int
        """
        float_fields = {
            "elements_ratios",
            "lattice_vectors",
            "cartesian_site_positions",
        }

        # Add existing attributes
        missing_attributes = cls.ALL_ATTRIBUTES.copy()
        existing_attributes = set(retrieved_attributes.keys())
        missing_attributes.difference_update(existing_attributes)
        for field in float_fields:
            if field in existing_attributes and retrieved_attributes.get(field):
                retrieved_attributes[field] = hex_to_floats(retrieved_attributes[field])
        res = retrieved_attributes.copy()

        # Create and add new attributes
        if missing_attributes:
            translator = cls.TRANSLATORS[node_type](entry_pk)
            for attribute in missing_attributes:
                try:
                    create_attribute = getattr(translator, attribute)
                except AttributeError as exc:
                    if attribute in cls.REQUIRED_ATTRIBUTES:
                        translator = None
                        raise NotImplementedError(
                            f"Parsing required attribute {attribute!r} from "
                            f"{translator.__class__.__name__} has not yet been "
                            "implemented."
                        ) from exc

                    warnings.warn(
                        f"Parsing optional attribute {attribute!r} from "
                        f"{translator.__class__.__name__} has not yet been "
                        "implemented.",
                        NotImplementedWarning,
                    )
                else:
                    res[attribute] = create_attribute()
            # Store new attributes in `extras`
            translator.store_attributes()
            del translator

        return res
