# pylint: disable=import-error
import pytest

from lark.exceptions import VisitError

from optimade.filterparser import LarkParser
from optimade.server.exceptions import BadRequest

from aiida_optimade.transformers import AiidaTransformer

VERSION = (1, 1, 0)
VARIANT = "default"

PARSER = LarkParser(version=VERSION, variant=VARIANT)
TRANSFORMER = AiidaTransformer()


def transform(filter_value: str):
    """Transform `filter` value using TRANSFORMER and PARSER"""
    return TRANSFORMER.transform(PARSER.parse(filter_value))


def test_empty():
    """Check passing "empty" strings"""
    assert transform(" ") is None
    assert transform("") is None


def test_property_names():
    """Check `property` names"""
    assert transform("band_gap = 1") == {"band_gap": {"==": 1}}
    assert transform("cell_length_a = 1") == {"cell_length_a": {"==": 1}}
    assert transform("cell_volume = 1") == {"cell_volume": {"==": 1}}

    with pytest.raises(BadRequest):
        transform("0_kvak IS KNOWN")  # starts with a number

    with pytest.raises(BadRequest):
        transform('"foo bar" IS KNOWN')  # contains space; contains quotes

    with pytest.raises(BadRequest):
        transform("BadLuck IS KNOWN")  # contains upper-case letters

    # database-provider-specific prefixes
    assert transform("_exmpl_formula_sum = 1") == {"_exmpl_formula_sum": {"==": 1}}
    assert transform("_exmpl_band_gap = 1") == {"_exmpl_band_gap": {"==": 1}}

    # Nested property names
    assert transform("identifier1.identifierd2 = 42") == {
        "identifier1.identifierd2": {"==": 42}
    }


def test_string_values():
    """Check various string values validity"""
    assert transform('author="Sąžininga Žąsis"') == {
        "author": {"==": "Sąžininga Žąsis"}
    }
    assert transform('field = "!#$%&\'() * +, -./:; <= > ? @[] ^ `{|}~ % "') == {
        "field": {"==": "!#$%&'() * +, -./:; <= > ? @[] ^ `{|}~ % "}
    }


def test_number_values():
    """Check various number values validity"""
    assert transform("a = 12345") == {"a": {"==": 12345}}
    assert transform("b = +12") == {"b": {"==": 12}}
    assert transform("c = -34") == {"c": {"==": -34}}
    assert transform("d = 1.2") == {"d": {"==": (1.2).hex()}}
    assert transform("e = .2E7") == {"e": {"==": (2000000.0).hex()}}
    assert transform("f = -.2E+7") == {"f": {"==": (-2000000.0).hex()}}
    assert transform("g = +10.01E-10") == {"g": {"==": (1.001e-09).hex()}}
    assert transform("h = 6.03e23") == {"h": {"==": (6.03e23).hex()}}
    assert transform("i = .1E1") == {"i": {"==": (1.0).hex()}}
    assert transform("j = -.1e1") == {"j": {"==": (-1.0).hex()}}
    assert transform("k = 1.e-12") == {"k": {"==": (1e-12).hex()}}
    assert transform("l = -.1e-12") == {"l": {"==": (-1e-13).hex()}}
    assert transform("m = 1000000000.E1000000000") == {"m": {"==": float("inf").hex()}}

    with pytest.raises(BadRequest):
        transform("number=1.234D12")
    with pytest.raises(BadRequest):
        transform("number=.e1")
    with pytest.raises(BadRequest):
        transform("number= -.E1")
    with pytest.raises(BadRequest):
        transform("number=+.E2")
    with pytest.raises(BadRequest):
        transform("number=1.23E+++")
    with pytest.raises(BadRequest):
        transform("number=+-123")
    with pytest.raises(BadRequest):
        transform("number=0.0.1")


def test_simple_comparisons():
    """Check simple comparisons"""
    assert transform("a<3") == {"a": {"<": 3}}
    assert transform("a<=3") == {"a": {"<=": 3}}
    assert transform("a>3") == {"a": {">": 3}}
    assert transform("a>=3") == {"a": {">=": 3}}
    assert transform("a=3") == {"a": {"==": 3}}
    assert transform("a!=3") == {"a": {"!==": 3}}


def test_id():
    """Test `id` valued `property` name"""
    assert transform('id="example/1"') == {"id": {"==": "example/1"}}
    assert transform('"example/1" = id') == {"id": {"==": "example/1"}}
    assert transform('id="test/2" OR "example/1" = id') == {
        "or": [{"id": {"==": "test/2"}}, {"id": {"==": "example/1"}}]
    }


def test_operators():
    """Test OPTIMADE filter operators"""
    # Basic boolean operations
    # TODO: {"!and": [{"a": {"<": 3}}]} can be simplified to {"a": {">=": 3}}
    assert transform("NOT a<3") == {"!and": [{"a": {"<": 3}}]}

    # TODO: {'!and': [{'a': {'==': 'Ti'}}]} can be simplified to {'a': {'!==': 'Ti'}}
    assert transform(
        "NOT ( "
        'chemical_formula_hill = "Al" AND chemical_formula_anonymous = "A" OR '
        'chemical_formula_anonymous = "H2O" AND NOT chemical_formula_hill = '
        '"Ti" )'
    ) == {
        "!and": [
            {
                "or": [
                    {
                        "and": [
                            {"chemical_formula_hill": {"==": "Al"}},
                            {"chemical_formula_anonymous": {"==": "A"}},
                        ]
                    },
                    {
                        "and": [
                            {"chemical_formula_anonymous": {"==": "H2O"}},
                            {"!and": [{"chemical_formula_hill": {"==": "Ti"}}]},
                        ]
                    },
                ]
            }
        ]
    }

    # Numeric and String comparisons
    assert transform("nelements > 3") == {"nelements": {">": 3}}
    assert transform(
        'chemical_formula_hill = "H2O" AND chemical_formula_anonymous != "AB"'
    ) == {
        "and": [
            {"chemical_formula_hill": {"==": "H2O"}},
            {"chemical_formula_anonymous": {"!==": "AB"}},
        ]
    }
    assert transform(
        "_exmpl_aax <= +.1e8 OR nelements >= 10 AND "
        'NOT ( _exmpl_x != "Some string" OR NOT _exmpl_a = 7)'
    ) == {
        "or": [
            {"_exmpl_aax": {"<=": (10000000.0).hex()}},
            {
                "and": [
                    {"nelements": {">=": 10}},
                    {
                        "!and": [
                            {
                                "or": [
                                    {"_exmpl_x": {"!==": "Some string"}},
                                    {"!and": [{"_exmpl_a": {"==": 7}}]},
                                ]
                            }
                        ]
                    },
                ]
            },
        ]
    }
    assert transform('_exmpl_spacegroup="P2"') == {"_exmpl_spacegroup": {"==": "P2"}}
    assert transform("_exmpl_cell_volume<100.0") == {
        "_exmpl_cell_volume": {"<": (100.0).hex()}
    }
    assert transform("_exmpl_bandgap > 5.0 AND _exmpl_molecular_weight < 350") == (
        {
            "and": [
                {"_exmpl_bandgap": {">": (5.0).hex()}},
                {"_exmpl_molecular_weight": {"<": 350}},
            ]
        }
    )
    assert transform(
        '_exmpl_melting_point<300 AND nelements=4 AND elements="Si,O2"'
    ) == {
        "and": [
            {"_exmpl_melting_point": {"<": 300}},
            {"nelements": {"==": 4}},
            {"elements": {"==": "Si,O2"}},
        ]
    }
    assert transform("_exmpl_some_string_property = 42") == (
        {"_exmpl_some_string_property": {"==": 42}}
    )
    assert transform("5 < _exmpl_a") == {"_exmpl_a": {">": 5}}

    assert transform("a<5 AND b=0") == {"and": [{"a": {"<": 5}}, {"b": {"==": 0}}]}
    assert transform("a >= 8 OR a<5 AND b>=8") == (
        {"or": [{"a": {">=": 8}}, {"and": [{"a": {"<": 5}}, {"b": {">=": 8}}]}]}
    )

    # OPTIONAL
    # assert transform("((NOT (_exmpl_a>_exmpl_b)) AND _exmpl_x>0)") == {}

    assert transform("NOT (a>1 AND b>1)") == {
        "!and": [{"and": [{"a": {">": 1}}, {"b": {">": 1}}]}]
    }

    assert transform("NOT (a>1 AND b>1 OR c>1)") == {
        "!and": [{"or": [{"and": [{"a": {">": 1}}, {"b": {">": 1}}]}, {"c": {">": 1}}]}]
    }

    assert transform("NOT (a>1 AND ( b>1 OR c>1 ))") == {
        "!and": [{"and": [{"a": {">": 1}}, {"or": [{"b": {">": 1}}, {"c": {">": 1}}]}]}]
    }

    assert transform("NOT (a>1 AND ( b>1 OR (c>1 AND d>1 ) ))") == {
        "!and": [
            {
                "and": [
                    {"a": {">": 1}},
                    {
                        "or": [
                            {"b": {">": 1}},
                            {"and": [{"c": {">": 1}}, {"d": {">": 1}}]},
                        ]
                    },
                ]
            }
        ]
    }

    assert transform(
        'elements HAS "Ag" AND NOT ( elements HAS "Ir" AND elements HAS "Ac" )'
    ) == {
        "and": [
            {"elements": {"contains": ["Ag"]}},
            {
                "!and": [
                    {
                        "and": [
                            {"elements": {"contains": ["Ir"]}},
                            {"elements": {"contains": ["Ac"]}},
                        ]
                    }
                ]
            },
        ]
    }

    assert transform("5 < 7") == {7: {">": 5}}

    with pytest.raises(VisitError):
        transform('"some string" > "some other string"')


@pytest.mark.skip("Relationships have not yet been implemented")
def test_filtering_on_relationships():
    """Test the nested properties with special names like "structures",
    "references" etc. are applied to the relationships field"""

    assert transform('references.id HAS "dummy/2019"') == (
        {"relationships.references.data.id": {"contains": ["dummy/2019"]}}
    )

    assert transform('structures.id HAS ANY "dummy/2019", "dijkstra1968"') == (
        {
            "relationships.structures.data.id": {
                "contains": ["dummy/2019", "dijkstra1968"]
            }
        }
    )

    assert transform('structures.id HAS ALL "dummy/2019", "dijkstra1968"') == (
        {
            "relationships.structures.data.id": {
                "contains": ["dummy/2019", "dijkstra1968"]
            }
        }
    )

    # NOTE: HAS ONLY has not yet been implemented.
    # assert transform('structures.id HAS ONLY "dummy/2019"') == (
    #     {
    #         "and": [
    #             {"relationships.structures.data": {"$size": 1}},
    #             {"relationships.structures.data.id": {
    #                 "contains": ["dummy/2019"]}
    #             },
    #         ]
    #     }
    # )

    # assert transform(
    #             'structures.id HAS ONLY "dummy/2019" AND structures.id HAS '
    #             '"dummy/2019"'
    #         ) == (
    #     {
    #         "and": [
    #             {
    #                 "and": [
    #                     {"relationships.structures.data": {"$size": 1}},
    #                     {
    #                         "relationships.structures.data.id": {
    #                             "contains": ["dummy/2019"]
    #                         }
    #                     },
    #                 ]
    #             },
    #             {"relationships.structures.data.id": {
    #                 "contains": ["dummy/2019"]}
    #             },
    #         ],
    #     }
    # )


def test_not_implemented():
    """Test list properties that are currently not implemented give a sensible
    response"""
    # NOTE: Lark catches underlying filtertransformer exceptions and
    # raises VisitErrors, most of these actually correspond to NotImplementedError
    with pytest.raises(VisitError, match="not been implemented"):
        transform("list HAS < 3")

    with pytest.raises(VisitError, match="not been implemented"):
        transform("list HAS ALL < 3, > 3")

    with pytest.raises(VisitError, match="not been implemented"):
        transform("list HAS ANY > 3, < 6")

    with pytest.raises(VisitError):
        transform("list:list HAS >=2:<=5")

    with pytest.raises(VisitError):
        transform(
            'elements:_exmpl_element_counts HAS "H":6 AND elements:'
            '_exmpl_element_counts HAS ALL "H":6,"He":7 AND elements:'
            '_exmpl_element_counts HAS ONLY "H":6 AND elements:'
            '_exmpl_element_counts HAS ANY "H":6,"He":7 AND elements:'
            '_exmpl_element_counts HAS ONLY "H":6,"He":7'
        )

    with pytest.raises(VisitError):
        transform(
            "_exmpl_element_counts HAS < 3 AND _exmpl_element_counts "
            "HAS ANY > 3, = 6, 4, != 8"
        )

    with pytest.raises(VisitError):
        transform(
            "elements:_exmpl_element_counts:_exmpl_element_weights "
            'HAS ANY > 3:"He":>55.3 , = 6:>"Ti":<37.6 , 8:<"Ga":0'
        )


def test_unaliased_length_operator():
    """Check unaliased LENGTH lists"""

    assert transform("cartesian_site_positions LENGTH 3") == (
        {"cartesian_site_positions": {"of_length": 3}}
    )
    assert transform("cartesian_site_positions LENGTH <= 3") == (
        {"cartesian_site_positions": {"or": [{"shorter": 3}, {"of_length": 3}]}}
    )
    assert transform("cartesian_site_positions LENGTH < 3") == (
        {"cartesian_site_positions": {"shorter": 3}}
    )
    assert transform("cartesian_site_positions LENGTH > 10") == (
        {"cartesian_site_positions": {"longer": 10}}
    )
    assert transform("cartesian_site_positions LENGTH >= 10") == (
        {"cartesian_site_positions": {"or": [{"longer": 10}, {"of_length": 10}]}}
    )


def test_list_properties():
    """Test the HAS ALL, ANY and optional ONLY queries"""
    # NOTE: HAS ONLY has not yet been implemented.
    # assert transform('elements HAS ONLY "H","He","Ga","Ta"') == (
    #     {"elements": {"contains": ["H", "He", "Ga", "Ta"], "$size": 4}}
    # )

    assert transform('elements HAS ANY "H","He","Ga","Ta"') == (
        {
            "elements": {
                "or": [
                    {"contains": ["H"]},
                    {"contains": ["He"]},
                    {"contains": ["Ga"]},
                    {"contains": ["Ta"]},
                ]
            }
        }
    )

    assert transform('elements HAS ALL "H","He","Ga","Ta"') == (
        {"elements": {"contains": ["H", "He", "Ga", "Ta"]}}
    )

    # assert transform(
    #             'elements HAS "H" AND elements HAS ALL "H","He","Ga","Ta" AND '
    #             'elements HAS ONLY "H","He","Ga","Ta" AND elements HAS ANY "H", '
    #             '"He", "Ga", "Ta"'
    #         ) == (
    #     {
    #         "and": [
    #             {"elements": {"contains": ["H"]}},
    #             {"elements": {"contains": ["H", "He", "Ga", "Ta"]}},
    #             {"elements": {"contains": ["H", "He", "Ga", "Ta"], "$size": 4}},
    #             {"elements": {"contains": ["H", "He", "Ga", "Ta"]}},
    #         ]
    #     }
    # )


def test_properties():
    """Filtering on Properties with unknown value"""
    # The { !and: [{ >: 1.99 }] } is different from the <= operator.
    # { <=: 1.99 } returns only the documents where price field exists and its
    # value is less than or equal to 1.99.
    # Remember that the !and operator only affects other operators and cannot check
    # fields and documents independently.
    # So, use the !and operator for logical disjunctions and the !== operator to
    # test the contents of fields directly.
    # source: https://docs.mongodb.com/manual/reference/operator/query/not/

    assert transform(
        "chemical_formula_hill IS KNOWN AND NOT chemical_formula_anonymous IS "
        "UNKNOWN"
    ) == {
        "and": [
            {"chemical_formula_hill": {"!==": None}},
            {"!and": [{"chemical_formula_anonymous": {"==": None}}]},
        ]
    }


def test_precedence():
    """Check OPERATOR precedence"""
    assert transform('NOT a > b OR c = 100 AND f = "C2 H6"') == (
        {
            "or": [
                {"!and": [{"a": {">": "b"}}]},
                {"and": [{"c": {"==": 100}}, {"f": {"==": "C2 H6"}}]},
            ]
        }
    )
    assert transform('NOT a > b OR c = 100 AND f = "C2 H6"') == (
        transform('(NOT (a > b)) OR ( (c = 100) AND (f = "C2 H6") )')
    )
    assert transform("a >= 0 AND NOT b < c OR c = 0") == (
        transform("((a >= 0) AND (NOT (b < c))) OR (c = 0)")
    )


def test_special_cases():
    """Check special cases"""
    assert transform("te < st") == {"te": {"<": "st"}}
    assert transform('spacegroup="P2"') == {"spacegroup": {"==": "P2"}}
    assert transform("_cod_cell_volume<100.0") == {
        "_cod_cell_volume": {"<": (100.0).hex()}
    }
    assert transform("_mp_bandgap > 5.0 AND _cod_molecular_weight < 350") == (
        {
            "and": [
                {"_mp_bandgap": {">": (5.0).hex()}},
                {"_cod_molecular_weight": {"<": 350}},
            ]
        }
    )
    assert transform('_cod_melting_point<300 AND nelements=4 AND elements="Si,O2"') == {
        "and": [
            {"_cod_melting_point": {"<": 300}},
            {"nelements": {"==": 4}},
            {"elements": {"==": "Si,O2"}},
        ]
    }
    assert transform("key=value") == {"key": {"==": "value"}}
    assert transform('author=" someone "') == {"author": {"==": " someone "}}
    assert transform("notice=val") == {"notice": {"==": "val"}}
    assert transform("NOTice=val") == {"!and": [{"ice": {"==": "val"}}]}
    assert transform(
        "number=0.ANDnumber=.0ANDnumber=0.0ANDnumber=+0AND_n_u_m_b_e_r_=-0AND"
        "number=0e1ANDnumber=0e-1ANDnumber=0e+1"
    ) == {
        "and": [
            {"number": {"==": (0.0).hex()}},
            {"number": {"==": (0.0).hex()}},
            {"number": {"==": (0.0).hex()}},
            {"number": {"==": 0}},
            {"_n_u_m_b_e_r_": {"==": 0}},
            {"number": {"==": (0.0).hex()}},
            {"number": {"==": (0.0).hex()}},
            {"number": {"==": (0.0).hex()}},
        ]
    }
