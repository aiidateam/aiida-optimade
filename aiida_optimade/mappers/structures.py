from optimade.models import StructureResourceAttributes
from aiida_optimade.parsers.structures import StructureDataParser

from .entries import ResourceMapper


__all__ = ("StructureMapper",)


class StructureMapper(ResourceMapper):
    """Map 'structure' resources from OPTiMaDe to AiiDA"""

    ALIASES = (
        ("immutable_id", "uuid"),
        ("last_modified", "mtime"),
        ("type", "extras.something.non.existing.type"),
    )
    PARSER = StructureDataParser
    ALL_ATTRIBUTES = list(StructureResourceAttributes.schema().get("properties").keys())
    REQUIRED_ATTRIBUTES = StructureResourceAttributes.schema().get("required")

    @classmethod
    def map_back(cls, entity_properties: dict) -> dict:
        """Map properties from AiiDA to OPTiMaDe

        :return: A resource object in OPTiMaDe format
        """

        mapping = ((real, alias) for alias, real in cls.ALIASES)
        new_object_attributes = {}
        new_object = {}

        for real, alias in mapping:
            if real in entity_properties and alias != "type":
                new_object_attributes[alias] = entity_properties[real]

        # Particular attributes
        # Remove "extras.optimade." prefix from reals to create aliases
        reals = []
        for field, value in entity_properties.items():
            if field.startswith(cls.PROJECT_PREFIX):
                if value is None:
                    continue
                reals.append(field)
        for real in reals:
            alias = real[len(cls.PROJECT_PREFIX) :]
            new_object_attributes[alias] = entity_properties[real]

        if "id" in entity_properties:
            new_object["id"] = entity_properties["id"]

        new_object["attributes"] = cls.build_attributes(new_object_attributes)

        new_object["type"] = "structures"
        return new_object

    @classmethod
    def build_attributes(cls, retrieved_attributes: dict) -> dict:
        """Build attributes dictionary for OPTiMaDe structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict
        """

        try:
            entry_uuid = retrieved_attributes["immutable_id"]
        except KeyError:
            raise KeyError(
                f'"immutable_id" should be present in retrieved_attributes: {retrieved_attributes}'
            )

        res = {}
        # Gather all available information for entry.
        missing_attributes = cls.ALL_ATTRIBUTES.copy()
        for existing_attribute, value in retrieved_attributes.items():
            res[existing_attribute] = value
            if existing_attribute in missing_attributes:
                missing_attributes.remove(existing_attribute)
        parser = cls.PARSER()
        for attribute in missing_attributes:
            try:
                create_attribute = getattr(parser, attribute)
            except AttributeError:
                if attribute in cls.REQUIRED_ATTRIBUTES:
                    parser = None
                    raise NotImplementedError(
                        f"Parsing required {attribute} from "
                        f"{cls.PARSER} has not yet been implemented."
                    )
                # Print warning that parsing non-required attribute has not yet been implemented
            else:
                res[attribute] = create_attribute(entry_uuid)

        parser = None
        return res
