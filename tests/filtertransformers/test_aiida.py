import unittest
import pytest

from lark.exceptions import VisitError

from optimade.filterparser import LarkParser, ParserError
from optimade.server.mappers import BaseResourceMapper

from aiida_optimade.transformers import AiidaTransformer


class TestAiidaTransformer(unittest.TestCase):
    """Tests for AiidaTransformer"""

    version = (0, 10, 1)
    variant = "default"
    maxDiff = None

    def setUp(self):
        parser = LarkParser(version=self.version, variant=self.variant)
        transformer = AiidaTransformer()
        self.transform = lambda inp: transformer.transform(parser.parse(inp))

    def test_empty(self):
        """Check passing "empty" strings"""
        self.assertIsNone(self.transform(" "))
        self.assertIsNone(self.transform(""))

    def test_property_names(self):
        """Check `property` names"""
        self.assertEqual(self.transform("band_gap = 1"), {"band_gap": {"==": 1}})
        self.assertEqual(
            self.transform("cell_length_a = 1"), {"cell_length_a": {"==": 1}}
        )
        self.assertEqual(self.transform("cell_volume = 1"), {"cell_volume": {"==": 1}})

        with self.assertRaises(ParserError):
            self.transform("0_kvak IS KNOWN")  # starts with a number

        with self.assertRaises(ParserError):
            self.transform('"foo bar" IS KNOWN')  # contains space; contains quotes

        with self.assertRaises(ParserError):
            self.transform("BadLuck IS KNOWN")  # contains upper-case letters

        # database-provider-specific prefixes
        self.assertEqual(
            self.transform("_exmpl_formula_sum = 1"), {"_exmpl_formula_sum": {"==": 1}}
        )
        self.assertEqual(
            self.transform("_exmpl_band_gap = 1"), {"_exmpl_band_gap": {"==": 1}}
        )

        # Nested property names
        self.assertEqual(
            self.transform("identifier1.identifierd2 = 42"),
            {"identifier1.identifierd2": {"==": 42}},
        )

    def test_string_values(self):
        """Check various string values validity"""
        self.assertEqual(
            self.transform('author="Sąžininga Žąsis"'),
            {"author": {"==": "Sąžininga Žąsis"}},
        )
        self.assertEqual(
            self.transform('field = "!#$%&\'() * +, -./:; <= > ? @[] ^ `{|}~ % "'),
            {"field": {"==": "!#$%&'() * +, -./:; <= > ? @[] ^ `{|}~ % "}},
        )

    def test_number_values(self):
        """Check various number values validity"""
        self.assertEqual(self.transform("a = 12345"), {"a": {"==": 12345}})
        self.assertEqual(self.transform("b = +12"), {"b": {"==": 12}})
        self.assertEqual(self.transform("c = -34"), {"c": {"==": -34}})
        self.assertEqual(self.transform("d = 1.2"), {"d": {"==": 1.2}})
        self.assertEqual(self.transform("e = .2E7"), {"e": {"==": 2000000.0}})
        self.assertEqual(self.transform("f = -.2E+7"), {"f": {"==": -2000000.0}})
        self.assertEqual(self.transform("g = +10.01E-10"), {"g": {"==": 1.001e-09}})
        self.assertEqual(self.transform("h = 6.03e23"), {"h": {"==": 6.03e23}})
        self.assertEqual(self.transform("i = .1E1"), {"i": {"==": 1.0}})
        self.assertEqual(self.transform("j = -.1e1"), {"j": {"==": -1.0}})
        self.assertEqual(self.transform("k = 1.e-12"), {"k": {"==": 1e-12}})
        self.assertEqual(self.transform("l = -.1e-12"), {"l": {"==": -1e-13}})
        self.assertEqual(
            self.transform("m = 1000000000.E1000000000"), {"m": {"==": float("inf")}}
        )

        with self.assertRaises(ParserError):
            self.transform("number=1.234D12")
        with self.assertRaises(ParserError):
            self.transform("number=.e1")
        with self.assertRaises(ParserError):
            self.transform("number= -.E1")
        with self.assertRaises(ParserError):
            self.transform("number=+.E2")
        with self.assertRaises(ParserError):
            self.transform("number=1.23E+++")
        with self.assertRaises(ParserError):
            self.transform("number=+-123")
        with self.assertRaises(ParserError):
            self.transform("number=0.0.1")

    def test_simple_comparisons(self):
        """Check simple comparisons"""
        self.assertEqual(self.transform("a<3"), {"a": {"<": 3}})
        self.assertEqual(self.transform("a<=3"), {"a": {"<=": 3}})
        self.assertEqual(self.transform("a>3"), {"a": {">": 3}})
        self.assertEqual(self.transform("a>=3"), {"a": {">=": 3}})
        self.assertEqual(self.transform("a=3"), {"a": {"==": 3}})
        self.assertEqual(self.transform("a!=3"), {"a": {"!==": 3}})

    def test_id(self):
        """Test `id` valued `property` name"""
        self.assertEqual(self.transform('id="example/1"'), {"id": {"==": "example/1"}})
        self.assertEqual(
            self.transform('"example/1" = id'), {"id": {"==": "example/1"}}
        )
        self.assertEqual(
            self.transform('id="test/2" OR "example/1" = id'),
            {"or": [{"id": {"==": "test/2"}}, {"id": {"==": "example/1"}}]},
        )

    def test_operators(self):
        """Test OPTIMADE filter operators"""
        # Basic boolean operations
        # TODO: {"!and": [{"a": {"<": 3}}]} can be simplified to {"a": {">=": 3}}
        self.assertEqual(self.transform("NOT a<3"), {"!and": [{"a": {"<": 3}}]})

        # TODO: {'!and': [{'==': 'Ti'}]} can be simplified to {'!==': 'Ti'}
        self.assertEqual(
            self.transform(
                "NOT ( "
                'chemical_formula_hill = "Al" AND chemical_formula_anonymous = "A" OR '
                'chemical_formula_anonymous = "H2O" AND NOT chemical_formula_hill = '
                '"Ti" )'
            ),
            {
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
            },
        )

        # Numeric and String comparisons
        self.assertEqual(self.transform("nelements > 3"), {"nelements": {">": 3}})
        self.assertEqual(
            self.transform(
                'chemical_formula_hill = "H2O" AND chemical_formula_anonymous != "AB"'
            ),
            {
                "and": [
                    {"chemical_formula_hill": {"==": "H2O"}},
                    {"chemical_formula_anonymous": {"!==": "AB"}},
                ]
            },
        )
        self.assertEqual(
            self.transform(
                "_exmpl_aax <= +.1e8 OR nelements >= 10 AND "
                'NOT ( _exmpl_x != "Some string" OR NOT _exmpl_a = 7)'
            ),
            {
                "or": [
                    {"_exmpl_aax": {"<=": 10000000.0}},
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
            },
        )
        self.assertEqual(
            self.transform('_exmpl_spacegroup="P2"'),
            {"_exmpl_spacegroup": {"==": "P2"}},
        )
        self.assertEqual(
            self.transform("_exmpl_cell_volume<100.0"),
            {"_exmpl_cell_volume": {"<": 100.0}},
        )
        self.assertEqual(
            self.transform("_exmpl_bandgap > 5.0 AND _exmpl_molecular_weight < 350"),
            {
                "and": [
                    {"_exmpl_bandgap": {">": 5.0}},
                    {"_exmpl_molecular_weight": {"<": 350}},
                ]
            },
        )
        self.assertEqual(
            self.transform(
                '_exmpl_melting_point<300 AND nelements=4 AND elements="Si,O2"'
            ),
            {
                "and": [
                    {"_exmpl_melting_point": {"<": 300}},
                    {"nelements": {"==": 4}},
                    {"elements": {"==": "Si,O2"}},
                ]
            },
        )
        self.assertEqual(
            self.transform("_exmpl_some_string_property = 42"),
            {"_exmpl_some_string_property": {"==": 42}},
        )
        self.assertEqual(self.transform("5 < _exmpl_a"), {"_exmpl_a": {">": 5}})

        self.assertEqual(
            self.transform("a<5 AND b=0"), {"and": [{"a": {"<": 5}}, {"b": {"==": 0}}]},
        )
        self.assertEqual(
            self.transform("a >= 8 OR a<5 AND b>=8"),
            {"or": [{"a": {">=": 8}}, {"and": [{"a": {"<": 5}}, {"b": {">=": 8}}]},]},
        )

        # OPTIONAL
        # self.assertEqual(
        #     self.transform("((NOT (_exmpl_a>_exmpl_b)) AND _exmpl_x>0)"), {}
        # )

        self.assertEqual(
            self.transform("NOT (a>1 AND b>1)"),
            {"!and": [{"and": [{"a": {">": 1}}, {"b": {">": 1}}]}]},
        )

        self.assertEqual(
            self.transform("NOT (a>1 AND b>1 OR c>1)"),
            {
                "!and": [
                    {
                        "or": [
                            {"and": [{"a": {">": 1}}, {"b": {">": 1}}]},
                            {"c": {">": 1}},
                        ]
                    }
                ]
            },
        )

        self.assertEqual(
            self.transform("NOT (a>1 AND ( b>1 OR c>1 ))"),
            {
                "!and": [
                    {
                        "and": [
                            {"a": {">": 1}},
                            {"or": [{"b": {">": 1}}, {"c": {">": 1}}]},
                        ]
                    }
                ]
            },
        )

        self.assertEqual(
            self.transform("NOT (a>1 AND ( b>1 OR (c>1 AND d>1 ) ))"),
            {
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
            },
        )

        self.assertEqual(
            self.transform(
                'elements HAS "Ag" AND NOT ( elements HAS "Ir" AND elements HAS "Ac" )'
            ),
            {
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
            },
        )

        self.assertEqual(self.transform("5 < 7"), {7: {">": 5}})

        with self.assertRaises(VisitError):
            self.transform('"some string" > "some other string"')

    @pytest.mark.skip("Relationships have not yet been implemented")
    def test_filtering_on_relationships(self):
        """Test the nested properties with special names like "structures",
        "references" etc. are applied to the relationships field"""

        self.assertEqual(
            self.transform('references.id HAS "dummy/2019"'),
            {"relationships.references.data.id": {"contains": ["dummy/2019"]}},
        )

        self.assertEqual(
            self.transform('structures.id HAS ANY "dummy/2019", "dijkstra1968"'),
            {
                "relationships.structures.data.id": {
                    "contains": ["dummy/2019", "dijkstra1968"]
                }
            },
        )

        self.assertEqual(
            self.transform('structures.id HAS ALL "dummy/2019", "dijkstra1968"'),
            {
                "relationships.structures.data.id": {
                    "contains": ["dummy/2019", "dijkstra1968"]
                }
            },
        )

        # NOTE: HAS ONLY has not yet been implemented.
        # self.assertEqual(
        #     self.transform('structures.id HAS ONLY "dummy/2019"'),
        #     {
        #         "and": [
        #             {"relationships.structures.data": {"$size": 1}},
        #             {"relationships.structures.data.id": {
        #                 "contains": ["dummy/2019"]}
        #             },
        #         ]
        #     },
        # )

        # self.assertEqual(
        #     self.transform(
        #         'structures.id HAS ONLY "dummy/2019" AND structures.id HAS '
        #         '"dummy/2019"'
        #     ),
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
        #     },
        # )

    def test_not_implemented(self):
        """Test list properties that are currently not implemented give a sensible
        response"""
        # NOTE: Lark catches underlying filtertransformer exceptions and
        # raises VisitErrors, most of these actually correspond to NotImplementedError
        with self.assertRaises(VisitError):
            try:
                self.transform("list HAS < 3")
            except Exception as exc:
                self.assertTrue("not been implemented" in repr(exc))
                raise exc

        with self.assertRaises(VisitError):
            try:
                self.transform("list HAS ALL < 3, > 3")
            except Exception as exc:
                self.assertTrue("not been implemented" in repr(exc))
                raise exc

        with self.assertRaises(VisitError):
            try:
                self.transform("list HAS ANY > 3, < 6")
            except Exception as exc:
                self.assertTrue("not been implemented" in repr(exc))
                raise exc

        with self.assertRaises(VisitError):
            self.transform("list:list HAS >=2:<=5")

        with self.assertRaises(VisitError):
            self.transform(
                'elements:_exmpl_element_counts HAS "H":6 AND elements:'
                '_exmpl_element_counts HAS ALL "H":6,"He":7 AND elements:'
                '_exmpl_element_counts HAS ONLY "H":6 AND elements:'
                '_exmpl_element_counts HAS ANY "H":6,"He":7 AND elements:'
                '_exmpl_element_counts HAS ONLY "H":6,"He":7'
            )

        with self.assertRaises(VisitError):
            self.transform(
                "_exmpl_element_counts HAS < 3 AND _exmpl_element_counts "
                "HAS ANY > 3, = 6, 4, != 8"
            )

        with self.assertRaises(VisitError):
            self.transform(
                "elements:_exmpl_element_counts:_exmpl_element_weights "
                'HAS ANY > 3:"He":>55.3 , = 6:>"Ti":<37.6 , 8:<"Ga":0'
            )

    @pytest.mark.skip("AiidaTransformer does not implement custom mapper")
    def test_list_length_aliases(self):
        """Check LENGTH aliases for lists"""
        from optimade.server.mappers import StructureMapper

        transformer = AiidaTransformer(mapper=StructureMapper())
        parser = LarkParser(version=self.version, variant=self.variant)

        self.assertEqual(
            transformer.transform(parser.parse("elements LENGTH 3")), {"nelements": 3}
        )

        self.assertEqual(
            transformer.transform(
                parser.parse('elements HAS "Li" AND elements LENGTH = 3')
            ),
            {"and": [{"elements": {"contains": ["Li"]}}, {"nelements": 3}]},
        )

        self.assertEqual(
            transformer.transform(parser.parse("elements LENGTH > 3")),
            {"nelements": {">": 3}},
        )
        self.assertEqual(
            transformer.transform(parser.parse("elements LENGTH < 3")),
            {"nelements": {"<": 3}},
        )
        self.assertEqual(
            transformer.transform(parser.parse("elements LENGTH = 3")), {"nelements": 3}
        )
        self.assertEqual(
            transformer.transform(parser.parse("cartesian_site_positions LENGTH <= 3")),
            {"nsites": {"<=": 3}},
        )
        self.assertEqual(
            transformer.transform(parser.parse("cartesian_site_positions LENGTH >= 3")),
            {"nsites": {">=": 3}},
        )

    def test_unaliased_length_operator(self):
        """Check unaliased LENGTH lists"""

        self.assertEqual(
            self.transform("cartesian_site_positions LENGTH 3"),
            {"cartesian_site_positions": {"of_length": 3}},
        )
        self.assertEqual(
            self.transform("cartesian_site_positions LENGTH <= 3"),
            {"cartesian_site_positions": {"or": [{"shorter": 3}, {"of_length": 3}]},},
        )
        self.assertEqual(
            self.transform("cartesian_site_positions LENGTH < 3"),
            {"cartesian_site_positions": {"shorter": 3}},
        )
        self.assertEqual(
            self.transform("cartesian_site_positions LENGTH > 10"),
            {"cartesian_site_positions": {"longer": 10}},
        )
        self.assertEqual(
            self.transform("cartesian_site_positions LENGTH >= 10"),
            {"cartesian_site_positions": {"or": [{"longer": 10}, {"of_length": 10}]},},
        )

    @pytest.mark.skip("AiidaTransformer does not implement custom mapper")
    def test_aliased_length_operator(self):
        """Test LENGTH operator alias"""
        from optimade.server.mappers import StructureMapper

        class MyMapper(StructureMapper):
            """Test mapper with LENGTH_ALIASES"""

            ALIASES = (("elements", "my_elements"), ("nelements", "nelem"))
            LENGTH_ALIASES = (
                ("chemsys", "nelements"),
                ("cartesian_site_positions", "nsites"),
                ("elements", "nelements"),
            )
            PROVIDER_FIELDS = ("chemsys",)

        transformer = AiidaTransformer(mapper=MyMapper())
        parser = LarkParser(version=self.version, variant=self.variant)

        self.assertEqual(
            transformer.transform(parser.parse("cartesian_site_positions LENGTH <= 3")),
            {"nsites": {"<=": 3}},
        )
        self.assertEqual(
            transformer.transform(parser.parse("cartesian_site_positions LENGTH < 3")),
            {"nsites": {"<": 3}},
        )
        self.assertEqual(
            transformer.transform(parser.parse("cartesian_site_positions LENGTH 3")),
            {"nsites": 3},
        )
        self.assertEqual(
            transformer.transform(parser.parse("cartesian_site_positions LENGTH 3")),
            {"nsites": 3},
        )
        self.assertEqual(
            transformer.transform(
                parser.parse("cartesian_site_positions LENGTH >= 10")
            ),
            {"nsites": {">=": 10}},
        )

        self.assertEqual(
            transformer.transform(parser.parse("structure_features LENGTH > 10")),
            {"structure_features": {"longer": 10}},
        )

        self.assertEqual(
            transformer.transform(parser.parse("nsites LENGTH > 10")),
            {"nsites": {"longer": 10}},
        )

        self.assertEqual(
            transformer.transform(parser.parse("elements LENGTH 3")), {"nelem": 3},
        )

        self.assertEqual(
            transformer.transform(parser.parse('elements HAS "Ag"')),
            {"my_elements": {"contains": ["Ag"]}},
        )

        self.assertEqual(
            transformer.transform(parser.parse("chemsys LENGTH 3")), {"nelem": 3},
        )

    @pytest.mark.skip("AiidaTransformer does not implement custom mapper")
    def test_aliases(self):
        """Test that valid aliases are allowed, but do not affect r-values"""

        class MyStructureMapper(BaseResourceMapper):
            """Test mapper with ALIASES"""

            ALIASES = (
                ("elements", "my_elements"),
                ("A", "D"),
                ("B", "E"),
                ("C", "F"),
            )

        mapper = MyStructureMapper()
        transformer = AiidaTransformer(mapper=mapper)

        self.assertEqual(mapper.alias_for("elements"), "my_elements")

        test_filter = {"elements": {"contains": ["A", "B", "C"]}}
        self.assertEqual(
            transformer.postprocess(test_filter),
            {"my_elements": {"contains": ["A", "B", "C"]}},
        )
        test_filter = {"and": [{"elements": {"contains": ["A", "B", "C"]}}]}
        self.assertEqual(
            transformer.postprocess(test_filter),
            {"and": [{"my_elements": {"contains": ["A", "B", "C"]}}]},
        )
        test_filter = {"elements": "A"}
        self.assertEqual(transformer.postprocess(test_filter), {"my_elements": "A"})
        test_filter = ["A", "B", "C"]
        self.assertEqual(transformer.postprocess(test_filter), ["A", "B", "C"])

        test_filter = ["A", "elements", "C"]
        self.assertEqual(transformer.postprocess(test_filter), ["A", "elements", "C"])

    def test_list_properties(self):
        """Test the HAS ALL, ANY and optional ONLY queries"""
        # NOTE: HAS ONLY has not yet been implemented.
        # self.assertEqual(
        #     self.transform('elements HAS ONLY "H","He","Ga","Ta"'),
        #     {"elements": {"contains": ["H", "He", "Ga", "Ta"], "$size": 4}},
        # )

        self.assertEqual(
            self.transform('elements HAS ANY "H","He","Ga","Ta"'),
            {
                "elements": {
                    "or": [
                        {"contains": ["H"]},
                        {"contains": ["He"]},
                        {"contains": ["Ga"]},
                        {"contains": ["Ta"]},
                    ]
                }
            },
        )

        self.assertEqual(
            self.transform('elements HAS ALL "H","He","Ga","Ta"'),
            {"elements": {"contains": ["H", "He", "Ga", "Ta"]}},
        )

        # self.assertEqual(
        #     self.transform(
        #         'elements HAS "H" AND elements HAS ALL "H","He","Ga","Ta" AND '
        #         'elements HAS ONLY "H","He","Ga","Ta" AND elements HAS ANY "H", '
        #         '"He", "Ga", "Ta"'
        #     ),
        #     {
        #         "and": [
        #             {"elements": {"contains": ["H"]}},
        #             {"elements": {"contains": ["H", "He", "Ga", "Ta"]}},
        #             {"elements": {"contains": ["H", "He", "Ga", "Ta"], "$size": 4}},
        #             {"elements": {"contains": ["H", "He", "Ga", "Ta"]}},
        #         ]
        #     },
        # )

    def test_properties(self):
        """Filtering on Properties with unknown value"""
        # The { !and: [{ >: 1.99 }] } is different from the <= operator.
        # { <=: 1.99 } returns only the documents where price field exists and its
        # value is less than or equal to 1.99.
        # Remember that the !and operator only affects other operators and cannot check
        # fields and documents independently.
        # So, use the !and operator for logical disjunctions and the !== operator to
        # test the contents of fields directly.
        # source: https://docs.mongodb.com/manual/reference/operator/query/not/

        self.assertEqual(
            self.transform(
                "chemical_formula_hill IS KNOWN AND NOT chemical_formula_anonymous IS "
                "UNKNOWN"
            ),
            {
                "and": [
                    {"chemical_formula_hill": {"!==": None}},
                    {"!and": [{"chemical_formula_anonymous": {"==": None}}]},
                ]
            },
        )

    def test_precedence(self):
        """Check OPERATOR precedence"""
        self.assertEqual(
            self.transform('NOT a > b OR c = 100 AND f = "C2 H6"'),
            {
                "or": [
                    {"!and": [{"a": {">": "b"}}]},
                    {"and": [{"c": {"==": 100}}, {"f": {"==": "C2 H6"}}]},
                ]
            },
        )
        self.assertEqual(
            self.transform('NOT a > b OR c = 100 AND f = "C2 H6"'),
            self.transform('(NOT (a > b)) OR ( (c = 100) AND (f = "C2 H6") )'),
        )
        self.assertEqual(
            self.transform("a >= 0 AND NOT b < c OR c = 0"),
            self.transform("((a >= 0) AND (NOT (b < c))) OR (c = 0)"),
        )

    def test_special_cases(self):
        """Check special cases"""
        self.assertEqual(self.transform("te < st"), {"te": {"<": "st"}})
        self.assertEqual(
            self.transform('spacegroup="P2"'), {"spacegroup": {"==": "P2"}}
        )
        self.assertEqual(
            self.transform("_cod_cell_volume<100.0"),
            {"_cod_cell_volume": {"<": 100.0}},
        )
        self.assertEqual(
            self.transform("_mp_bandgap > 5.0 AND _cod_molecular_weight < 350"),
            {
                "and": [
                    {"_mp_bandgap": {">": 5.0}},
                    {"_cod_molecular_weight": {"<": 350}},
                ]
            },
        )
        self.assertEqual(
            self.transform(
                '_cod_melting_point<300 AND nelements=4 AND elements="Si,O2"'
            ),
            {
                "and": [
                    {"_cod_melting_point": {"<": 300}},
                    {"nelements": {"==": 4}},
                    {"elements": {"==": "Si,O2"}},
                ]
            },
        )
        self.assertEqual(self.transform("key=value"), {"key": {"==": "value"}})
        self.assertEqual(
            self.transform('author=" someone "'), {"author": {"==": " someone "}}
        )
        self.assertEqual(self.transform("notice=val"), {"notice": {"==": "val"}})
        self.assertEqual(
            self.transform("NOTice=val"), {"!and": [{"ice": {"==": "val"}}]}
        )
        self.assertEqual(
            self.transform(
                "number=0.ANDnumber=.0ANDnumber=0.0ANDnumber=+0AND_n_u_m_b_e_r_=-0AND"
                "number=0e1ANDnumber=0e-1ANDnumber=0e+1"
            ),
            {
                "and": [
                    {"number": {"==": 0.0}},
                    {"number": {"==": 0.0}},
                    {"number": {"==": 0.0}},
                    {"number": {"==": 0}},
                    {"_n_u_m_b_e_r_": {"==": 0}},
                    {"number": {"==": 0.0}},
                    {"number": {"==": 0.0}},
                    {"number": {"==": 0.0}},
                ]
            },
        )
