# pylint: disable=no-self-use,too-many-public-methods
from lark import Transformer, v_args


__all__ = ("AiidaTransformer",)

# Conversion map from the OPTIMADE operators to the QueryBuilder operators
OPERATOR_CONVERSION = {"=": "==", "!=": "!==", "in": "contains"}


def op_conv_map(operator):
    """Convert operator or return same operator"""
    return OPERATOR_CONVERSION.get(operator, operator)


class AiidaTransformer(Transformer):
    """Transform OPTIMADE query to AiiDA QueryBuilder queryhelp query"""

    reversed_operator_map = {
        "<": ">",
        "<=": ">=",
        ">": "<",
        ">=": "<=",
        "!=": "!==",
        "=": "==",
    }
    list_operator_map = {"<": "shorter", ">": "longer", "=": "of_length"}

    def __init__(self):
        super().__init__()

    def filter(self, arg):
        """filter: expression*"""
        return arg[0] if arg else None

    @v_args(inline=True)
    def constant(self, value):
        """constant: string | number"""
        # NOTE: Do nothing!
        return value

    @v_args(inline=True)
    def value(self, value):
        """value: string | number | property"""
        # NOTE: Do nothing!
        return value

    @v_args(inline=True)
    def non_string_value(self, value):
        """ non_string_value: number | property """
        # NOTE: Do nothing!
        return value

    @v_args(inline=True)
    def not_implemented_string(self, value):
        """not_implemented_string: value

        Raise NotImplementedError.
        For further information, see Materials-Consortia/OPTIMADE issue 157:
        https://github.com/Materials-Consortia/OPTIMADE/issues/157
        """
        raise NotImplementedError("Comparing strings is not yet implemented.")

    def value_list(self, args):
        """value_list: [ OPERATOR ] value ( "," [ OPERATOR ] value )*"""
        for value in args:
            if str(value) in self.reversed_operator_map:
                # value is OPERATOR
                # This is currently not supported
                raise NotImplementedError(
                    f"OPERATOR {value} inside value_list {args} has not been "
                    "implemented."
                )

        return args

    def value_zip(self, arg):
        """
        value_zip: [ OPERATOR ] value ":" [ OPERATOR ] value (":" [ OPERATOR ] value)*
        """
        raise NotImplementedError

    def value_zip_list(self, arg):
        """
        value_zip_list: value_zip ( "," value_zip )*
        """
        raise NotImplementedError

    def expression(self, arg):
        """
        expression: expression_clause ( OR expression_clause )
        expression with and without 'OR'
        """
        return {"or": arg} if len(arg) > 1 else arg[0]

    def expression_clause(self, arg):
        """
        expression_clause: expression_phrase ( AND expression_phrase )*
        expression_clause with and without 'AND'
        """
        return {"and": arg} if len(arg) > 1 else arg[0]

    def expression_phrase(self, arg):
        """
        expression_phrase: [ NOT ] ( comparison | "(" expression ")" )
        """
        if len(arg) == 1:
            # without NOT
            return arg[0]

        # with NOT
        return {"!and": [arg[1]]}

    @v_args(inline=True)
    def comparison(self, value):
        """
        comparison: constant_first_comparison | property_first_comparison
        """
        # NOTE: Do nothing!
        return value

    def property_first_comparison(self, arg):
        """
        property_first_comparison: property ( value_op_rhs |
                                              known_op_rhs |
                                              fuzzy_string_op_rhs |
                                              set_op_rhs |
                                              set_zip_op_rhs |
                                              length_op_rhs )
        """
        return {arg[0]: arg[1]}

    def constant_first_comparison(self, arg):
        """
        constant_first_comparison: constant OPERATOR ( non_string_value |
                                                       not_implemented_string )
        """
        return {arg[2]: {self.reversed_operator_map[arg[1]]: arg[0]}}

    @v_args(inline=True)
    def value_op_rhs(self, operator, value):
        """
        value_op_rhs: OPERATOR value
        """
        return {op_conv_map(operator.value): value}

    def known_op_rhs(self, arg):
        """
        known_op_rhs: IS ( KNOWN | UNKNOWN )
        """
        if arg[1] == "KNOWN":
            key = "!=="
        elif arg[1] == "UNKNOWN":
            key = "=="
        else:
            raise NotImplementedError(
                f"Unknown operator: {arg[1]}. Must be either KNOWN or UNKNOWN."
            )
        return {key: None}

    def fuzzy_string_op_rhs(self, arg):
        """
        fuzzy_string_op_rhs: CONTAINS string |
                             STARTS [ WITH ] string |
                             ENDS [ WITH ] string
        """
        # Since the string pattern will always be the last argument,
        # and there is always another keyword before the OPTIONAL "WITH",
        # there is no need to test for the existence of "WITH"
        if arg[0] == "CONTAINS":
            like = f"%{arg[-1]}%"
        elif arg[0] == "STARTS":
            like = f"{arg[-1]}%"
        elif arg[0] == "ENDS":
            like = f"%{arg[-1]}"
        else:
            raise NotImplementedError(
                f"Unknown fuzzy string operator: {arg[0]}. "
                "Must be either CONTAINS, STARTS or ENDS."
            )
        return {"like": like}

    def set_op_rhs(self, arg):
        """
        set_op_rhs: HAS ( [ OPERATOR ] value |
                          ALL value_list |
                          ANY value_list |
                          ONLY value_list )
        """
        if len(arg) == 2:
            # only value without OPERATOR
            return {"contains": [arg[1]]}

        if arg[1] == "ALL":
            return {"contains": arg[2]}
        if arg[1] == "ANY":
            return {"or": [{"contains": [value]} for value in arg[2]]}
        if arg[1] == "ONLY":
            raise NotImplementedError(
                "`set_op_rhs HAS ONLY value_list` has not been implemented."
            )

        # value with OPERATOR
        raise NotImplementedError(
            f"set_op_rhs has not been implemented for use with OPERATOR. Given: {arg}"
        )

    def set_zip_op_rhs(self, arg):
        """
        set_zip_op_rhs: property_zip_addon HAS ( value_zip |
                                                 ONLY value_zip_list |
                                                 ALL value_zip_list |
                                                 ANY value_zip_list )
        """
        raise NotImplementedError

    def length_op_rhs(self, arg):
        """
        length_op_rhs: LENGTH [ OPERATOR ] value
        """
        if len(arg) == 3:
            operator = arg[1].value
        else:
            operator = "="

        if operator in self.list_operator_map:
            return {self.list_operator_map[operator]: arg[-1]}

        if operator in {">=", "<="}:
            return {
                "or": [
                    {self.list_operator_map[operator[0]]: arg[-1]},
                    {self.list_operator_map[operator[1]]: arg[-1]},
                ]
            }

        raise NotImplementedError(
            f"Operator {operator} has not been implemented for the LENGTH filter."
        )

    def property_zip_addon(self, arg):
        """
        property_zip_addon: ":" property (":" property)*
        """
        raise NotImplementedError

    def property(self, arg):
        """
        property: IDENTIFIER ( "." IDENTIFIER )*
        """
        return ".".join(arg)

    @v_args(inline=True)
    def string(self, string):
        """
        string: ESCAPED_STRING
        """
        return string.strip('"')

    @v_args(inline=True)
    def signed_int(self, number):
        """
        signed_int: SIGNED_INT
        """
        return int(number)

    @v_args(inline=True)
    def signed_float(self, number):
        """
        signed_float: SIGNED_FLOAT

        All floats values are converted and stored as hex strings in AiiDA.
        """
        return float(number).hex()

    @v_args(inline=True)
    def number(self, number):
        """
        number: SIGNED_INT | SIGNED_FLOAT

        All floats values are converted and stored as hex strings in AiiDA.
        """
        if number.type == "SIGNED_INT":
            return int(number)
        if number.type == "SIGNED_FLOAT":
            return float(number).hex()

        raise NotImplementedError(
            f"number: {number} (type: {number.type}) does not seem to be a SIGNED_INT "
            "or SIGNED_FLOAT"
        )

    def __default__(self, data, children, meta):  # pragma: no cover
        raise NotImplementedError(
            "Calling __default__, i.e., unknown grammar concept. "
            f"data: {data}, children: {children}, meta: {meta}"
        )
