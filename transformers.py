# -*- coding: utf-8 -*-

from lark import Transformer


class TreeToPy(Transformer):

    # def VALUE(self, s):
    #     if isinstance(s, str):
    #         return token.value()
    #     elif isinstance(s, int):
    #         return int(s)
    #     elif isinstance(s, float):
    #         return float(s)
    #     else:
    #         raise
    # def OPERATOR(self, o):
    #     return str(o[1:-1])
    # def KEYWORD(self, s):
    #     self.assertEqual(s, "test")
    #     self.assertTrue(1==2)
    #     print("from KEYWORD")
    #     return str(s)
    # def AND(self, o):
    #     return o.value()
    # def OR(self, o):
    #     return str(o)
    # def NOT(self, o):
    #     return str(o)

    start = tuple
    expression = list
    term = list
    atom = list
    andcomparison = list
    comparison = tuple

    def null(self, _):
        return None

    def true(self, _):
        return True

    def false(self, _):
        return False

    # def VALUE(self, )
    #     pass
    # pass
