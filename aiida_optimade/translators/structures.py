# pylint: disable=line-too-long
import itertools

from typing import List, Union
from aiida.orm import StructureData

from aiida_optimade.common import OptimadeIntegrityError, AiidaError

from .entities import AiidaEntityTranslator


__all__ = ("StructureDataTranslator",)


class StructureDataTranslator(AiidaEntityTranslator):
    """Create OPTIMADE "structures" attributes from an AiiDA StructureData Node

    Each OPTIMADE field is a method in this class.

    NOTE: This class succeeds in *never* loading the actual AiiDA Node for optimization purposes.
    """

    AIIDA_ENTITY = StructureData

    # StructureData specific properties
    def __init__(self, uuid: str):
        super().__init__(uuid)

        self.__kinds = None
        self.__sites = None

    @property
    def _kinds(self) -> list:
        if not self.__kinds:
            self.__kinds = self._get_unique_node_property("attributes.kinds")
        return self.__kinds

    @property
    def _sites(self) -> list:
        if not self.__sites:
            self.__sites = self._get_unique_node_property("attributes.sites")
        return self.__sites

    # Helper methods to calculate OPTIMADE fields
    def get_symbols_set(self):
        """Copy of aiida.orm.StructureData:get_symbols_set()"""
        return set(
            itertools.chain.from_iterable(kind["symbols"] for kind in self._kinds)
        )

    def has_vacancies(self):
        """Copy of aiida.orm.StructureData:has_vacancies"""
        from aiida.orm.nodes.data.structure import _sum_threshold

        def kind_has_vacancies(weights):
            """Copy of aiida.orm.Kinds:has_vacancies"""
            w_sum = sum(weights)
            return not 1.0 - w_sum < _sum_threshold

        return any(kind_has_vacancies(kind["weights"]) for kind in self._kinds)

    def get_formula(self, mode="hill", separator=""):
        """Copy of aiida.orm.StructureData:get_formula()"""
        from aiida.orm.nodes.data.structure import get_symbols_string, get_formula

        symbol_list = []
        for site in self._sites:
            for _kind in self._kinds:
                if _kind["name"] == site["kind_name"]:
                    kind = _kind
                    break
            else:
                raise AiidaError(
                    f"kind with name {site['kind_name']} cannot be found amongst the kinds {self._kinds}"
                )
            symbol_list.append(get_symbols_string(kind["symbols"], kind["weights"]))

        return get_formula(symbol_list, mode=mode, separator=separator)

    def get_symbol_weights(self) -> dict:
        """Get weights of all symbols / chemical elements"""
        occupation = {}.fromkeys(sorted(self.get_symbols_set()), 0.0)
        for kind in self._kinds:
            number_of_sites = len(
                [_ for _ in self._sites if _["kind_name"] == kind["name"]]
            )
            for i in range(len(kind["symbols"])):
                occupation[kind["symbols"][i]] += kind["weights"][i] * number_of_sites
        return occupation

    def has_partial_occupancy(self) -> bool:
        """Check for partial occupancies (first vacancies, next through element ratios)"""
        if self.has_vacancies():
            return True

        occupation = self.get_symbol_weights()
        for occ in occupation.values():
            if not occ.is_integer():
                return True

        for kind in self._kinds:
            if len(kind["weights"]) > 1:
                return True

        return False

    def check_floating_round_errors(self, some_list: List[Union[List, float]]) -> list:
        """Check whether there are some float rounding errors (check only for close to zero numbers)

        :param some_list: Must be a list of either lists or float values
        :type some_list: list
        """
        might_as_well_be_zero = (
            1e-8  # This is for Å, so 1e-8 Å can by all means be considered 0 Å
        )
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
    def elements(self) -> List[str]:
        """Names of elements found in the structure as a list of strings, in alphabetical order."""
        attribute = "elements"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = sorted(self.get_symbols_set())

        # If there are vacancies present, remove them
        if "X" in res:
            res.remove("X")

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def nelements(self) -> int:
        """Number of different elements in the structure as an integer."""
        attribute = "nelements"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = len(self.elements())

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def elements_ratios(self) -> List[float]:
        """Relative proportions of different elements in the structure."""
        attribute = "elements_ratios"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        ratios = self.get_symbol_weights()

        total_weight = sum(ratios.values())
        res = [ratios[symbol] / total_weight for symbol in self.elements()]

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = str(res)
        return res

    def chemical_formula_descriptive(self) -> str:
        """The chemical formula for a structure as a string in a form chosen by the API implementation."""
        attribute = "chemical_formula_descriptive"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = self.get_formula()

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def chemical_formula_reduced(self) -> str:
        """The reduced chemical formula for a structure

        As a string with element symbols and integer chemical proportion numbers.
        The proportion number MUST be omitted if it is 1.

        NOTE: For structures with partial occupation, the chemical proportion numbers are integers
        that within reasonable approximation indicate the correct chemical proportions.
        The precise details of how to perform the rounding is chosen by the API implementation.
        """
        attribute = "chemical_formula_reduced"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        occupation = self.get_symbol_weights()
        for symbol, weight in occupation.items():
            rounded_weight = round(weight)
            if rounded_weight in {0, 1}:
                occupation[symbol] = ""
            else:
                occupation[symbol] = rounded_weight
        values = [_ for _ in occupation.values() if _]
        if len(values) == len(occupation.values()):
            min_occupation = min(values)
            for symbol, weight in occupation.items():
                weight = weight / min_occupation
                rounded_weight = round(weight)
                if rounded_weight in {0, 1}:
                    occupation[symbol] = ""
                else:
                    occupation[symbol] = rounded_weight
        res = "".join([f"{symbol}{occupation[symbol]}" for symbol in self.elements()])

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def chemical_formula_hill(self) -> str:
        """The chemical formula for a structure in Hill form

        With element symbols followed by integer chemical proportion numbers.
        The proportion number MUST be omitted if it is 1.

        NOTE: If the system has sites with partial occupation and the total occupations
        of each element do not all sum up to integers, then the Hill formula SHOULD be handled as unset.

        NOTE: This will always be equal to chemical_formula_descriptive if it should not be handled as unset.
        """
        attribute = "chemical_formula_hill"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        if self.has_partial_occupancy():
            res = None
        else:
            res = self.get_formula(mode="hill")

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def chemical_formula_anonymous(self) -> str:
        """The anonymous formula is the chemical_formula_reduced

        But where the elements are instead first ordered by their chemical proportion number,
        and then, in order left to right, replaced by anonymous symbols:
        A, B, C, ..., Z, Aa, Ba, ..., Za, Ab, Bb, ... and so on.
        """
        import string

        attribute = "chemical_formula_anonymous"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        elements = self.elements()
        nelements = self.nelements()

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
        map_anonymous = dict(zip(elements, anonymous_elements))

        occupation = self.get_symbol_weights()
        for symbol, weight in occupation.items():
            rounded_weight = round(weight)
            if rounded_weight == 1:
                occupation[symbol] = ""
            else:
                occupation[symbol] = rounded_weight
        res = "".join(
            [f"{map_anonymous[symbol]}{occupation[symbol]}" for symbol in elements]
        )

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def dimension_types(self) -> List[int]:
        """List of three integers.

        For each of the three directions indicated by the three lattice vectors
        (see property lattice_vectors). This list indicates if the direction is periodic (value 1)
        or non-periodic (value 0). Note: the elements in this list each refer to the direction
        of the corresponding entry in property lattice_vectors and not the Cartesian x, y, z directions.
        """
        attribute = "dimension_types"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = [
            int(value)
            for value in (
                self._get_unique_node_property(f"attributes.pbc{i + 1}")
                for i in range(3)
            )
        ]

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def nperiodic_dimensions(self) -> int:
        """Number of periodic dimensions."""
        attribute = "nperiodic_dimensions"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = sum(
            [
                int(value)
                for value in (
                    self._get_unique_node_property(f"attributes.pbc{i + 1}")
                    for i in range(3)
                )
            ]
        )

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def lattice_vectors(self) -> List[List[float]]:
        """The three lattice vectors in Cartesian coordinates, in ångström (Å)."""
        attribute = "lattice_vectors"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = self.check_floating_round_errors(
            self._get_unique_node_property("attributes.cell")
        )

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def cartesian_site_positions(self) -> List[List[Union[float, None]]]:
        """Cartesian positions of each site.

        A site is an atom, a site potentially occupied by an atom,
        or a placeholder for a virtual mixture of atoms (e.g., in a virtual crystal approximation).
        """
        attribute = "cartesian_site_positions"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        sites = [list(site["position"]) for site in self._sites]
        res = self.check_floating_round_errors(sites)

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def nsites(self) -> int:
        """An integer specifying the length of the cartesian_site_positions property."""
        attribute = "nsites"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = len(self.cartesian_site_positions())

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def species_at_sites(self) -> List[str]:
        """Name of the species at each site

        (Where values for sites are specified with the same order of the property
        cartesian_site_positions). The properties of the species are found in the property species.
        """
        attribute = "species_at_sites"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = [site["kind_name"] for site in self._sites]

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    def species(self) -> List[dict]:
        """A list describing the species of the sites of this structure.

        Species can be pure chemical elements, or virtual-crystal atoms
        representing a statistical occupation of a given site by multiple chemical elements.
        """
        import re

        attribute = "species"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = []

        # Create a species
        for kind in self._kinds:
            name = kind["name"]
            kind_weight_sum = 0

            # Retrieve elements in 'kind'
            for i in range(len(kind["symbols"])):
                weight = kind["weights"][i]

                # Accumulating sum of weights
                kind_weight_sum += weight

            species = {
                "name": name,
                "chemical_symbols": list(kind["symbols"]),
                "concentration": list(kind["weights"]),
                "mass": kind.get("mass", 0),
                "original_name": name,
            }

            if re.match(r".*X(?!e).*", name):
                # Species includes/is a vacancy
                species["chemical_symbols"].append("vacancy")

                # Calculate vacancy concentration
                if 0.0 <= kind_weight_sum <= 1.0:
                    species["concentration"].append(1.0 - kind_weight_sum)
                else:
                    raise ValueError("kind_weight_sum must be in the interval [0;1]")

            res.append(species)

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res

    # def assemblies(self) -> List[dict]:
    #     """A description of groups of sites that are statistically correlated."""
    #     attribute = "assemblies"

    #     if attribute in self.new_attributes:
    #         return self.new_attributes[attribute]

    #     res = []

    #     # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
    #     self.new_attributes[attribute] = res
    #     return res

    def structure_features(self) -> List[str]:
        """A list of strings that flag which special features are used by the structure.

        SHOULD be absent if there are no partial occupancies
        """
        attribute = "structure_features"

        if attribute in self.new_attributes:
            return self.new_attributes[attribute]

        res = []

        # Figure out if there are partial occupancies
        if not self.has_partial_occupancy():
            self.new_attributes[attribute] = res
            return res

        # * Disorder *
        # This flag MUST be present if any one entry in the species list
        # has a chemical_symbols list that is longer than 1 element.
        species = self.species()
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
        cartesian_site_positions = self.cartesian_site_positions()
        for site in cartesian_site_positions:
            if float("NaN") in site:
                res.append("unknown_positions")
                break

        # * Assemblies *
        # This flag MUST be present if the property assemblies is present.
        # if self.assemblies():
        #     res.append("assemblies")

        # Finally, save OPTIMADE attribute for later storage in extras for AiiDA Node and return value
        self.new_attributes[attribute] = res
        return res
