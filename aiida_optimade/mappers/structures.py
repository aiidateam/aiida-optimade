from optimade.models import StructureResourceAttributes

from aiida_optimade.translators import StructureDataTranslator

from .entries import ResourceMapper


__all__ = ("StructureMapper",)


class StructureMapper(ResourceMapper):
    """Map 'structure' resources from OPTiMaDe to AiiDA"""

    ENDPOINT = "structures"
    ALIASES = (
        ("immutable_id", "uuid"),
        ("last_modified", "mtime"),
        ("type", "attributes.something.non.existing"),
        ("relationships", "attributes.something.non.existing"),
        ("links", "attributes.something.non.existing"),
    )
    TRANSLATOR = StructureDataTranslator
    ALL_ATTRIBUTES = list(StructureResourceAttributes.schema().get("properties").keys())
    REQUIRED_ATTRIBUTES = StructureResourceAttributes.schema().get("required")

    @classmethod
    def map_back(cls, entity_properties: dict) -> dict:
        """Map properties from AiiDA to OPTiMaDe

        :param entity_properties: Found AiiDA properties through QueryBuilder query
        :type entity_properties: dict

        :return: A resource object in OPTiMaDe format
        :rtype: dict
        """
        mapping = ((real, alias) for alias, real in cls.all_aliases())

        new_object_attributes = {}
        new_object = {}

        for real, alias in mapping:
            if (
                real in entity_properties
                and entity_properties[real] is not None
                and alias not in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS
            ):
                new_object_attributes[alias] = entity_properties[real]

        # We always need "id"
        if "id" not in entity_properties:
            raise KeyError(
                f'"id" should be present in entity_properties: {entity_properties}'
            )

        for field in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS:
            value = entity_properties.get(field, None)
            if value is not None:
                new_object[field] = value

        new_object["attributes"] = cls.build_attributes(
            new_object_attributes, new_object["id"]
        )
        new_object["type"] = cls.ENDPOINT

        return new_object

    @classmethod
    def build_attributes(cls, retrieved_attributes: dict, entry_pk: int) -> dict:
        """Build attributes dictionary for OPTiMaDe structure resource

        :param retrieved_attributes: Dict of new attributes, will be updated accordingly
        :type retrieved_attributes: dict

        :param entry_pk: The AiiDA Node's PK
        :type entry_pk: int
        """
        import json

        res = {}
        float_fields_stored_as_strings = {"elements_ratios"}
        # Add existing attributes
        # TODO: Use sets instead!!
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
                            f"Parsing required {attribute} from "
                            f"{cls.TRANSLATOR} has not yet been implemented."
                        )
                    # Print warning that parsing non-required attribute has not yet
                    # been implemented
                else:
                    res[attribute] = create_attribute()
            # Store new attributes in `extras`
            translator.store_attributes()
            translator = None

        return res
