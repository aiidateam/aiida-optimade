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
    REQUIRED_FIELDS = set(StructureResourceAttributes.schema().get("required"))

    # pylint: disable=too-many-locals
    @classmethod
    def build_attributes(
        cls,
        retrieved_attributes: dict,
        desired_attributes: set,
        entry_pk: int,
        node_type: str,
    ) -> dict:
        """Build attributes dictionary for OPTIMADE structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict

        :param desired_attributes: List of attributes to be built.
        :type desired_attributes: set

        :param entry_pk: The AiiDA Node's PK
        :type entry_pk: int

        :param node_type: The AiiDA Node's type
        :type node_type: str
        """
        float_fields = {
            "elements_ratios",
            "lattice_vectors",
            "cartesian_site_positions",
        }

        # Add existing attributes
        existing_attributes = set(retrieved_attributes.keys())
        desired_attributes.difference_update(existing_attributes)
        for field in float_fields:
            if field in existing_attributes and retrieved_attributes.get(field):
                retrieved_attributes[field] = hex_to_floats(retrieved_attributes[field])
        res = retrieved_attributes.copy()

        none_value_attributes = cls.REQUIRED_FIELDS - desired_attributes.union(
            existing_attributes
        )
        none_value_attributes = {
            _ for _ in none_value_attributes if not _.startswith("_")
        }
        res.update({field: None for field in none_value_attributes})

        # Create and add new attributes
        if desired_attributes:
            translator = cls.TRANSLATORS[node_type](entry_pk)

            for attribute in desired_attributes:
                try:
                    create_attribute = getattr(translator, attribute)
                except AttributeError as exc:
                    if attribute in cls.get_required_fields():
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

            # Special post-treatment for `structure_features`
            all_fields = (
                translator._get_optimade_extras()  # pylint: disable=protected-access
            )
            all_fields.update(translator.new_attributes)
            structure_features = all_fields.get("structure_features", [])
            if all_fields.get("species", None) is None:
                for feature in ["disorder", "implicit_atoms", "site_attachments"]:
                    try:
                        structure_features.remove(feature)
                    except ValueError:
                        # Not in list
                        pass
            if structure_features != all_fields.get("structure_features", []):
                # Some fields were removed
                translator.new_attributes["structure_features"] = structure_features

            translator.new_attributes.update(
                {field: None for field in none_value_attributes}
            )

            # Store new attributes in `extras`
            translator.store_attributes()
            del translator

        return res
