from typing import Dict
import warnings

from optimade.server.config import CONFIG

from aiida_optimade.common import NotImplementedWarning
from aiida_optimade.models import StructureResourceAttributes
from aiida_optimade.translators import (
    hex_to_floats,
    AiidaEntityTranslator,
    CifDataTranslator,
    StructureDataTranslator,
)

from aiida_optimade.mappers.entries import ResourceMapper


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
        cls,
        retrieved_attributes: dict,
        entry_pk: int,
        node_type: str,
        missing_attributes: set = None,
    ) -> dict:
        """Build attributes dictionary for OPTIMADE structure resource

        Parameters:
            retrieved_attributes: New attributes, will be updated accordingly.
            entry_pk: The AiiDA Node's PK (`Node.pk`)
            node_type: The AiiDA Node's type (`Node.node_type`)
            missing_attributes: Missing attributes to be calculated.
                If this is not supplied, it will be determined as the difference
                between `ALL_ATTRIBUTES` and the keys of `retrieved_attributes`.

        Returns:
            An updated dictionary based on `retrieved_attributes`, including all
            newly calculated fields.

        """
        float_fields = {
            "elements_ratios",
            "lattice_vectors",
            "cartesian_site_positions",
        }

        # Add existing attributes
        existing_attributes = set(retrieved_attributes.keys())
        if missing_attributes is None:
            missing_attributes = cls.ALL_ATTRIBUTES - existing_attributes
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
                    if not CONFIG.use_real_mongo:
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
                        warnings.warn(
                            f"Trying to parse attribute {attribute!r} from "
                            f"{translator.__class__.__name__}, but is has not been "
                            "implemented. This may be a mistake, but may also be fine, "
                            "since a MongoDB is used.",
                            NotImplementedWarning,
                        )
                else:
                    res[attribute] = create_attribute()
            # Store new attributes in Node extras or MongoDB collection
            translator.store_attributes(mongo=CONFIG.use_real_mongo)
            del translator

        return res
