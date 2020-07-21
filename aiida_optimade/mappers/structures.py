import warnings

from aiida_optimade.common import NotImplementedWarning
from aiida_optimade.models import StructureResourceAttributes
from aiida_optimade.translators import StructureDataTranslator

from .entries import ResourceMapper


__all__ = ("StructureMapper",)


class StructureMapper(ResourceMapper):
    """Map 'structure' resources from OPTIMADE to AiiDA"""

    ENDPOINT = "structures"

    TRANSLATOR = StructureDataTranslator
    ALL_ATTRIBUTES = set(StructureResourceAttributes.schema().get("properties").keys())
    REQUIRED_ATTRIBUTES = set(StructureResourceAttributes.schema().get("required"))

    @classmethod
    def build_attributes(cls, retrieved_attributes: dict, entry_pk: int) -> dict:
        """Build attributes dictionary for OPTIMADE structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict

        :param entry_pk: The AiiDA Node's PK
        :type entry_pk: int
        """
        import json

        res = {}
        float_fields_stored_as_strings = {"elements_ratios"}

        # Add existing attributes
        missing_attributes = cls.ALL_ATTRIBUTES.copy()
        for existing_attribute, value in retrieved_attributes.items():
            if existing_attribute in float_fields_stored_as_strings and value:
                value = json.loads(str(value))
            res[existing_attribute] = value
            if existing_attribute in missing_attributes:
                missing_attributes.remove(existing_attribute)

        # Create and add new attributes
        if missing_attributes:
            translator = cls.TRANSLATOR(entry_pk)
            for attribute in missing_attributes:
                try:
                    create_attribute = getattr(translator, attribute)
                except AttributeError:
                    if attribute in cls.REQUIRED_ATTRIBUTES:
                        translator = None
                        raise NotImplementedError(
                            f"Parsing required attribute {attribute!r} from "
                            f"{cls.TRANSLATOR} has not yet been implemented."
                        )

                    warnings.warn(
                        f"Parsing optional attribute {attribute!r} from "
                        f"{cls.TRANSLATOR} has not yet been implemented.",
                        NotImplementedWarning,
                    )
                else:
                    res[attribute] = create_attribute()
            # Store new attributes in `extras`
            translator.store_attributes()
            translator = None

        return res
