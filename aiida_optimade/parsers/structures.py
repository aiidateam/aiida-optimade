from typing import Any, List, Union
from aiida.orm import QueryBuilder, StructureData


class AiidaEntityNotFound(Exception):
    """Could not find an AiiDA entity in the DB."""


class DeductionError(Exception):
    """Cannot deduce the value of an attribute."""


class OptimadeIntegrityError(Exception):
    """A required OPTiMaDe attribute or sub-attribute may be missing.
    Or it may be that the internal data integrity is violated,
    i.e., number of "species_at_sites" does not equal "nsites"
    """


class StructureDataParser:
    """Create OPTiMaDe attributes from AiiDA StructureData Node

    For speed and reusability, save attributes in the Node's extras.
    Each OPTiMaDe should be a method in this class
    """

    EXTRAS_KEY = "optimade"
    AIIDA_ENTITY = StructureData

    NODE = None

    def _get_extras(self, uuid: str) -> dict:
        query = QueryBuilder(limit=1)
        query.append(self.AIIDA_ENTITY, filters={"uuid": uuid}, project="extras")
        if query.count() != 1:
            raise AiidaEntityNotFound(
                f"Could not find {self.AIIDA_ENTITY} with UUID {uuid}."
            )
        return query.first()[0]

    def _get_entity(self, uuid: str) -> StructureData:
        if not self.NODE or self.NODE.uuid != uuid:
            self.NODE = None
            query = QueryBuilder(limit=1).append(
                self.AIIDA_ENTITY, filters={"uuid": uuid}, project="*"
            )
            if query.count() != 1:
                raise AiidaEntityNotFound(
                    f"Could not find StructureData with UUID {uuid}. Found {query.count()} StructureData nodes."
                )
            self.NODE = query.first()[0]
        return self.NODE

    def _update_extras(self, uuid: str, optimade_attributes: dict):
        structure = self._get_entity(uuid)
        structure.set_extra(self.EXTRAS_KEY, optimade_attributes)

    def _save_extra(self, uuid: str, attribute: str, value: Any):
        extras = self._get_extras(uuid)

        try:
            optimade = extras[self.EXTRAS_KEY]
        except KeyError:
            # First time root extras key is created
            optimade = {attribute: value}
            self._update_extras(uuid, optimade)
            return
        else:
            optimade[attribute] = value
            self._update_extras(uuid, optimade)
            return

    def get_symbol_weights(self, node: StructureData) -> dict:
        occupation = {}.fromkeys(sorted(node.get_symbols_set()), 0.0)
        for kind in node.kinds:
            number_of_sites = len([_ for _ in node.sites if _.kind_name == kind.name])
            for i in range(len(kind.symbols)):
                occupation[kind.symbols[i]] += kind.weights[i] * number_of_sites
        return occupation

    def has_partial_occupancy(self, node: StructureData) -> bool:
        """Check for partial occupancies (first vacancies, next through element ratios)"""
        if node.has_vacancies:
            return True

        occupation = self.get_symbol_weights(node)
        for occ in occupation.values():
            if not occ.is_integer():
                return True

        return False

    def check_floating_round_errors(self, some_list: List[Union[List, float]]) -> list:
        """Check whether there are some float rounding errors (check only for close to zero numbers)

        :param some_list: Must be a list of either lists or float values
        :type some_list: list
        """
        might_as_well_be_zero = (
            1e-8
        )  # This is for Å, so 1e-8 Å can by all means be considered 0 Å
        res = []

        for item in some_list:
            vector = []
            for scalar in item:
                if isinstance(scalar, list):
                    res.append(self.check_floating_round_errors(item))
                else:
                    if scalar < might_as_well_be_zero:
                        scalar = 0
                    vector.append(scalar)
            res.append(vector)
        return res

    # Start creating fields
    def elements(self, uuid: str) -> List[str]:
        """Names of elements found in the structure as a list of strings, in alphabetical order."""

        attribute = "elements"

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

        # Create value from AiiDA Node
        res = len(self.elements(uuid))

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def elements_ratios(self, uuid: str) -> List[float]:
        """Relative proportions of different elements in the structure."""

        attribute = "elements_ratios"

        # Create value from AiiDA Node
        node = self._get_entity(uuid)

        ratios = self.get_symbol_weights(node)

        total_weight = sum(ratios.values())
        res = [ratios[symbol] / total_weight for symbol in self.elements(uuid)]

        # Make sure it sums to one
        should_be_zero = 1.0 - sum(res)
        if self.check_floating_round_errors([[should_be_zero]]) != [[0]]:
            raise DeductionError(
                f"Calculated {attribute} does not sum to float(1): {sum(res)}"
            )

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def chemical_formula_descriptive(self, uuid: str) -> str:
        """The chemical formula for a structure as a string in a form chosen by the API implementation."""

        attribute = "chemical_formula_descriptive"

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = node.get_formula()

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

        # Create value from AiiDA Node
        node = self._get_entity(uuid)

        occupation = self.get_symbol_weights(node)
        for symbol, weight in occupation.items():
            rounded_weight = round(weight)
            if rounded_weight in {0, 1}:
                occupation[symbol] = ""
            else:
                occupation[symbol] = rounded_weight
        res = "".join(
            [f"{symbol}{occupation[symbol]}" for symbol in self.elements(uuid)]
        )

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def chemical_formula_hill(self, uuid: str) -> str:
        """The chemical formula for a structure in Hill form

        With element symbols followed by integer chemical proportion numbers.
        The proportion number MUST be omitted if it is 1.

        NOTE: If the system has sites with partial occupation and the total occupations
        of each element do not all sum up to integers, then the Hill formula SHOULD be handled as unset.

        NOTE: This will always be equal to chemical_formula_descriptive if it should not be handled as unset.
        """

        attribute = "chemical_formula_hill"

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = node.get_formula(mode="hill")

        if self.has_partial_occupancy(node):
            res = None

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def chemical_formula_anonymous(  # pylint: disable=too-many-locals
        self, uuid: str
    ) -> str:
        """The anonymous formula is the chemical_formula_reduced

        But where the elements are instead first ordered by their chemical proportion number,
        and then, in order left to right, replaced by anonymous symbols:
        A, B, C, ..., Z, Aa, Ba, ..., Za, Ab, Bb, ... and so on.
        """
        import string

        attribute = "chemical_formula_anonymous"

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

        occupation = self.get_symbol_weights(node)
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

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = [int(value) for value in node.pbc]

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def lattice_vectors(self, uuid: str) -> List[List[float]]:
        """The three lattice vectors in Cartesian coordinates, in ångström (Å)."""

        attribute = "lattice_vectors"

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = self.check_floating_round_errors(node.cell)

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def cartesian_site_positions(self, uuid: str) -> List[List[Union[float, None]]]:
        """Cartesian positions of each site.

        A site is an atom, a site potentially occupied by an atom,
        or a placeholder for a virtual mixture of atoms (e.g., in a virtual crystal approximation).
        """

        attribute = "cartesian_site_positions"

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        sites = [list(site.position) for site in node.sites]
        res = self.check_floating_round_errors(sites)

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def nsites(self, uuid: str) -> int:
        """An integer specifying the length of the cartesian_site_positions property."""

        attribute = "nsites"

        # Create value from AiiDA Node
        res = len(self.cartesian_site_positions(uuid))

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def species_at_sites(self, uuid: str) -> List[str]:
        """Name of the species at each site

        (Where values for sites are specified with the same order of the property
        cartesian_site_positions). The properties of the species are found in the property species.
        """

        attribute = "species_at_sites"

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = [site.kind_name for site in node.sites]

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    def species(self, uuid: str) -> List[dict]:  # pylint: disable=too-many-locals
        """A list describing the species of the sites of this structure.

        Species can be pure chemical elements, or virtual-crystal atoms
        representing a statistical occupation of a given site by multiple chemical elements.
        """
        import re

        attribute = "species"

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = []

        # Create a species
        for kind in node.kinds:
            name = kind.name
            kind_weight_sum = 0

            # Retrieve elements in 'kind'
            for i in range(len(kind.symbols)):
                weight = kind.weights[i]

                # Accumulating sum of weights
                kind_weight_sum += weight

            species = {
                "name": name,
                "chemical_symbols": list(kind.symbols),
                "concentration": list(kind.weights),
                "mass": kind.mass,
                "original_name": name,
            }

            if re.match(r"[\w]*X[\d]*", name):
                # Species includes/is a vacancy
                species["chemical_symbols"].append("vacancy")

                # Calculate vacancy concentration
                if 0.0 <= kind_weight_sum <= 1.0:
                    species["concentration"].append(1.0 - kind_weight_sum)
                else:
                    raise ValueError("kind_weight_sum must be in the interval [0;1]")

            res.append(species)

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res

    # def assemblies(self, uuid: str) -> List[dict]:
    #     """A description of groups of sites that are statistically correlated."""

    #     attribute = "assemblies"

    #     # Create value from AiiDA Node
    #     node = self._get_entity(uuid)

    #     # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
    #     self._save_extra(uuid, attribute, res)
    #     return res

    def structure_features(self, uuid: str) -> List[str]:
        """A list of strings that flag which special features are used by the structure.

        SHOULD be absent if there are no partial occupancies
        """

        attribute = "structure_features"

        # Create value from AiiDA Node
        node = self._get_entity(uuid)
        res = []

        # Figure out if there are partial occupancies
        if not self.has_partial_occupancy(node):
            self._save_extra(uuid, attribute, res)
            return res

        # * Disorder *
        # This flag MUST be present if any one entry in the species list
        # has a chemical_symbols list that is longer than 1 element.
        species = self.species(uuid)
        key = "chemical_symbols"
        for item in species:
            if key not in item:
                raise OptimadeIntegrityError(
                    f'The required key {key} was not found for {item} in the "species" attribute'
                )
            if len(item[key]) > 1:
                res.append("disorder")
                break

        # * Unknown positions *
        # This flag MUST be present if at least one component of the cartesian_site_positions
        # list of lists has value null.
        cartesian_site_positions = self.cartesian_site_positions(uuid)
        for site in cartesian_site_positions:
            if float("NaN") in site:
                res.append("unknown_positions")
                break

        # * Assemblies *
        # This flag MUST be present if the property assemblies is present.
        # if self.assemblies(uuid):
        #     res.append("assemblies")

        # Finally, save OPTiMaDe attribute in extras for AiiDA Node and return value
        self._save_extra(uuid, attribute, res)
        return res
