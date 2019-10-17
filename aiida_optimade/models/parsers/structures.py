from typing import Any, List, Union
from aiida.orm import QueryBuilder, StructureData


class OptimadeAttributeNotFoundInExtras(Exception):
    """Could not find an OPTiMaDe attribute in extras, even though it should be there."""


class AiidaEntityNotFound(Exception):
    """Could not find an AiiDA entity in the DB."""


class DeductionError(Exception):
    """Cannot deduce the value of an attribute."""


class StructureDataParser:
    """Create OPTiMaDe attributes from AiiDA StructureData Node

    For speed and reusability, save attributes in the Node's extras.
    Each OPTiMaDe should be a method in this class
    """

    EXTRAS_KEY = "optimade"
    AIIDA_ENTITY = StructureData

    def _get_extras(self, uuid: str) -> dict:
        query = QueryBuilder(limit=1)
        query.append(self.AIIDA_ENTITY, filters={"uuid": uuid}, project="extras")
        if query.count() != 1:
            raise AiidaEntityNotFound(
                f"Could not find {self.AIIDA_ENTITY} with UUID {uuid}."
            )
        return query.first()[0]

    def _get_optimade_attribute(self, uuid: str, optimade_attribute: str) -> Any:
        try:
            return self._get_extras(uuid).get(self.EXTRAS_KEY, {})[optimade_attribute]
        except KeyError:
            raise OptimadeAttributeNotFoundInExtras(
                f"Cannot find {optimade_attribute} in extras.{self.EXTRAS_KEY} for {self.AIIDA_ENTITY} with UUID {uuid}."
            )

    def _optimade_attribute_exists(self, uuid: str, optimade_attribute: str) -> bool:
        try:
            self._get_extras(uuid)[self.EXTRAS_KEY][optimade_attribute]
        except KeyError:
            return False
        else:
            return True

    def _get_entity(self, uuid: str) -> StructureData:
        query = QueryBuilder(limit=1).append(
            self.AIIDA_ENTITY, filters={"uuid": uuid}, project="*"
        )
        if query.count() != 1:
            raise AiidaEntityNotFound(
                f"Could not find StructureData with UUID {uuid}. Found {query.count()} StructureData nodes."
            )
        return query.first()[0]

    def _update_extras(
        self, uuid: str, optimade_attributes: dict, attribute: str, value: Any
    ):
        structure = self._get_entity(uuid)
        structure.set_extra(self.EXTRAS_KEY, optimade_attributes)
        if not self._optimade_attribute_exists(uuid, attribute):
            raise OptimadeAttributeNotFoundInExtras(
                f'After setting extra "{self.EXTRAS_KEY}" with {optimade_attributes}, '
                f"the OPTiMaDe attribute {attribute} with the (new) value {value} "
                f"could not be found to exists. StructureData: {structure}"
            )

    def _save_extra(self, uuid: str, attribute: str, value: Any):
        extras = self._get_extras(uuid)

        try:
            optimade = extras[self.EXTRAS_KEY]
        except KeyError:
            # First time root extras key is created in extras
            optimade = {attribute: value}
            self._update_extras(uuid, optimade, attribute, value)
            return

        try:
            existing_value = optimade[attribute]
        except KeyError:
            # First time attribute is created in extras
            optimade[attribute] = value
            self._update_extras(uuid, optimade, attribute, value)
            return

        raise Exception(
            "Somehow reached this stage. "
            f"Existing value: {existing_value}. UUID: {uuid}. Attribute: {attribute}. "
            f"Value: {value}. Found extras: {extras}"
        )

        # if not isinstance(value, type(existing_value)):
        #     raise TypeError(f"Types of values are not the same. "
        #         f"\"existing_value\": type={type(existing_value)}, value={existing_value}; "
        #         f"\"value\": type={type(value)}, value={value}"
        #     )

        # if isinstance(value, list):
        #     if len(existing_value) != len(value):
        #         # Update attribute with new value
        #         optimade[attribute] = value
        #         self._update_extras(uuid, optimade, attribute, value)
        #         return

        #     for item in value:
        #         if item not in existing_value:
        #             # Update attribute with new value
        #             optimade[attribute] = value
        #             self._update_extras(uuid, optimade, attribute, value)
        #             return

        # if existing_value != value:
        #     # Update attribute with new value
        #     optimade[attribute] = value
        #     self._update_extras(uuid, optimade, attribute, value)

    def elements(self, uuid: str) -> List[str]:
        """Names of elements found in the structure as a list of strings, in alphabetical order."""

        attribute = "elements"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = sorted(node.get_symbols_set())

        # If there are vacancies present, remove them
        if "X" in res:
            res.remove("X")

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def nelements(self, uuid: str) -> int:
        """Number of different elements in the structure as an integer."""

        attribute = "nelements"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        res = len(self.elements(uuid))

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def elements_ratios(self, uuid: str) -> List[float]:
        """Relative proportions of different elements in the structure."""

        attribute = "elements_ratios"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        node = self._get_entity(uuid)

        elements = self.elements(uuid)
        ratios = {}.fromkeys(elements, 0.0)
        for kind in node.kinds:
            if len(kind.weights) > 1:
                raise DeductionError(
                    f"Cannot deal with multiple weights for a kind: {kind}. UUID: {uuid}"
                )
            ratios[kind.symbol] += kind.weights[0]

        total_weight = sum(ratios.values())
        res = [ratios[symbol] / total_weight for symbol in elements]

        # Make sure it sums to one
        if sum(res) != 1.0:
            raise DeductionError(
                f"Calculated {attribute} does not sum to float(1): {sum(res)}"
            )

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def chemical_formula_descriptive(self, uuid: str) -> str:
        """The chemical formula for a structure as a string in a form chosen by the API implementation."""

        attribute = "chemical_formula_descriptive"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = node.get_formula(mode="hill")

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def chemical_formula_reduced(self, uuid: str) -> str:
        """The reduced chemical formula for a structure

        As a string with element symbols and integer chemical proportion numbers.
        The proportion number MUST be omitted if it is 1.

        NOTE: For structures with partial occupation, the chemical proportion numbers are integers
        that within reasonable approximation indicate the correct chemical proportions.
        The precise details of how to perform the rounding is chosen by the API implementation.
        """

        attribute = "chemical_formula_reduced"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        node = self._get_entity(uuid)

        elements = self.elements(uuid)
        occupation = {}.fromkeys(elements, 0.0)
        for kind in node.kinds:
            if len(kind.weights) > 1:
                raise DeductionError(
                    f"Cannot deal with multiple weights for a kind: {kind}. UUID: {uuid}"
                )
            occupation[kind.symbol] += kind.weights[0]
        for symbol, weight in occupation.items():
            rounded_weight = round(weight)
            if rounded_weight == 1:
                occupation[symbol] = ""
            else:
                occupation[symbol] = rounded_weight
        res = "".join([f"{symbol}{occupation[symbol]}" for symbol in elements])

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def chemical_formula_hill(self, uuid: str) -> str:
        """The chemical formula for a structure in Hill form

        With element symbols followed by integer chemical proportion numbers.
        The proportion number MUST be omitted if it is 1.

        NOTE: If the system has sites with partial occupation and the total occupations
        of each element do not all sum up to integers, then the Hill formula SHOULD be handled as unset.

        NOTE: This will always be equal to chemical_formula_descriptive if it should not be handles as unset.
        """

        attribute = "chemical_formula_hill"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = node.get_formula(mode="hill")

        # Check for partial occupancies (first vacancies, next through element ratios)
        if node.has_vacancies:
            res = None

        elements = self.elements(uuid)
        occupation = {}.fromkeys(elements, 0.0)
        for kind in node.kinds:
            if len(kind.weights) > 1:
                raise DeductionError(
                    f"Cannot deal with multiple weights for a kind: {kind}. UUID: {uuid}"
                )
            occupation[kind.symbol] += kind.weights[0]
        for occ in occupation.values():
            if not occ.is_integer():
                res = None
                break

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def chemical_formula_anonymous(
        self, uuid: str
    ) -> str:  # pylint: disable=too-many-locals
        """The anonymous formula is the chemical_formula_reduced

        But where the elements are instead first ordered by their chemical proportion number,
        and then, in order left to right, replaced by anonymous symbols:
        A, B, C, ..., Z, Aa, Ba, ..., Za, Ab, Bb, ... and so on.
        """
        import string

        attribute = "chemical_formula_anonymous"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        elements = self.elements(uuid)
        nelements = self.nelements(uuid)

        anonymous_elements = []
        for i in range(nelements):
            symbol = string.ascii_uppercase[i % len(string.ascii_uppercase)]
            if i >= len(string.ascii_uppercase):
                symbol += string.ascii_lowercase[
                    (i - len(string.ascii_uppercase))
                    // len(string.ascii_lowercase)
                    % len(string.ascii_lowercase)
                ]
            # NOTE: This does not expect more than Zz elements (26+26*26 = 702) - should be enough ...
            anonymous_elements.append(symbol)
        map_anonymous = {
            symbol: new_symbol
            for symbol, new_symbol in zip(elements, anonymous_elements)
        }

        occupation = {}.fromkeys(elements, 0.0)
        for kind in node.kinds:
            if len(kind.weights) > 1:
                raise DeductionError(
                    f"Cannot deal with multiple weights for a kind: {kind}. UUID: {uuid}"
                )
            occupation[kind.symbol] += kind.weights[0]
        for symbol, weight in occupation.items():
            rounded_weight = round(weight)
            if rounded_weight == 1:
                occupation[symbol] = ""
            else:
                occupation[symbol] = rounded_weight
        res = "".join(
            [f"{map_anonymous[symbol]}{occupation[symbol]}" for symbol in elements]
        )

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def dimension_types(self, uuid: str) -> List[int]:
        """List of three integers.

        For each of the three directions indicated by the three lattice vectors
        (see property lattice_vectors). This list indicates if the direction is periodic (value 1)
        or non-periodic (value 0). Note: the elements in this list each refer to the direction
        of the corresponding entry in property lattice_vectors and not the Cartesian x, y, z directions.
        """

        attribute = "dimension_types"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = [int(value) for value in node.pbc]

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def lattice_vectors(self, uuid: str) -> List[List[float]]:
        """The three lattice vectors in Cartesian coordinates, in ångström (Å)."""

        attribute = "lattice_vectors"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        cell = node.cell

        # Check whether there are some float rounding "errors"
        might_as_well_be_zero = (
            1e-8
        )  # This is for Å, so 1e-8 Å can by all means be considered 0 Å
        res = []
        for vector in cell:
            res_vector = []
            for scalar in vector:
                if scalar < might_as_well_be_zero:
                    scalar = 0
                res_vector.append(scalar)
            res.append(res_vector)

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def cartesian_site_coordinates(self, uuid: str) -> List[List[Union[float, None]]]:
        """Cartesian positions of each site.

        A site is an atom, a site potentially occupied by an atom,
        or a placeholder for a virtual mixture of atoms (e.g., in a virtual crystal approximation).
        """

        attribute = "cartesian_site_coordinates"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        raise NotImplementedError(f"{attribute} not yet implemented")

        # # Create value from AiiDA Node
        # node = self._get_entity(uuid)

        # # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        # self._save_extra(uuid, attribute, res)
        # return res

    def nsites(self, uuid: str) -> int:
        """An integer specifying the length of the cartesian_site_positions property."""

        attribute = "nsites"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        # Create value from AiiDA Node
        res = len(self.cartesian_site_coordinates(uuid))

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def species_at_sites(self, uuid: str) -> List[str]:
        """Name of the species at each site

        (Where values for sites are specified with the same order of the property
        cartesian_site_positions). The properties of the species are found in the property species.
        """

        attribute = "species_at_sites"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        raise NotImplementedError(f"{attribute} not yet implemented")

        # # Create value from AiiDA Node
        # node = self._get_entity(uuid)

        # # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        # self._save_extra(uuid, attribute, res)
        # return res

    def species(self, uuid: str) -> List[dict]:
        """A list describing the species of the sites of this structure.

        Species can be pure chemical elements, or virtual-crystal atoms
        representing a statistical occupation of a given site by multiple chemical elements.
        """

        attribute = "species"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        raise NotImplementedError(f"{attribute} not yet implemented")

        # # Create value from AiiDA Node
        # node = self._get_entity(uuid)

        # # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        # self._save_extra(uuid, attribute, res)
        # return res

    def assemblies(self, uuid: str) -> List[dict]:
        """A description of groups of sites that are statistically correlated."""

        attribute = "assemblies"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        raise NotImplementedError(f"{attribute} not yet implemented")

        # # Create value from AiiDA Node
        # node = self._get_entity(uuid)

        # # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        # self._save_extra(uuid, attribute, res)
        # return res

    def structure_features(self, uuid: str) -> List[str]:
        """A list of strings that flag which special features are used by the structure."""

        attribute = "structure_features"

        # Return value if OPTiMaDe attribute has already been saved in extras for AiiDA Node
        if self._optimade_attribute_exists(uuid, attribute):
            return self._get_optimade_attribute(uuid, attribute)

        raise NotImplementedError(f"{attribute} not yet implemented")

        # # Create value from AiiDA Node
        # node = self._get_entity(uuid)

        # # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        # self._save_extra(uuid, attribute, res)
        # return res
