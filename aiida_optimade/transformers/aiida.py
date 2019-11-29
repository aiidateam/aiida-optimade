from lark import Transformer, v_args, Token


class TransformerError(Exception):
    """Error in transforming filter expression"""


__all__ = ("AiidaTransformerV0_9_7", "AiidaTransformerV0_10_1")

# Conversion map from the OPTiMaDe operators to the QueryBuilder operators
operator_conversion = {"=": "==", "!=": "!==", "in": "contains"}


def op_conv_map(operator):
    return operator_conversion.get(operator, operator)


def conjoin_args(args):
    """Conjoin from left to right.

    CONJUNCTION: AND | OR

    :param args: [<expression/term> CONJUNCTION] <term/atom>
    :type args: list

    :return: AiiDA QueryBuilder filter
    :rtype: dict
    """
    if len(args) == 1:  # Only <term>
        return args[0]

    conjunction = args[1].value.lower()
    return {conjunction: [args[0], args[2]]}


class AiidaTransformerV0_9_7(Transformer):
    """Transformer for AiiDA using QueryBuilder"""

    def start(self, args):
        return args[0]

    def expression(self, args):
        return conjoin_args(args)

    def term(self, args):
        if args[0] == "(":
            return conjoin_args(args[1:-1])
        return conjoin_args(args)

    def atom(self, args):
        """Optionally negate a comparison."""
        # Two cases:
        # 1. args is parsed comparison, or
        # 2. args is NOT token and parsed comparison
        #     - [ Token(NOT, 'not'), {field: {op: val}} ]
        #        -> {field: {!op: val}}
        if len(args) == 2:
            field, predicate = next(((k, v) for k, v in args[1].items()))
            for op in list(predicate.keys()):
                if op.startswith("!"):
                    not_op = op[1:]
                else:
                    not_op = "!" + op
                predicate[not_op] = predicate.pop(op)
            return {field: {"!in": predicate}}

        return args[0]

    def comparison(self, args):
        field = args[0].value
        if isinstance(args[2], list):
            if args[1].value != "=":
                raise NotImplementedError(
                    "x,y,z values only supported for '=' operator"
                )
            return {field: {"in": args[2]}}

        op = op_conv_map(args[1].value)
        value_token = args[2]
        try:
            value = float(value_token.value)
        except ValueError:
            value = value_token.value
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
        else:
            if value.is_integer():
                value = int(value)
        return {field: {op: value}}

    def combined(self, args):
        elements = []
        for value_token in args:
            try:
                value = float(value_token.value)
            except ValueError:
                value = value_token.value
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
            else:
                if value.is_integer():
                    value = int(value)
            elements.append(value)
        return elements


class AiidaTransformerV0_10_1(Transformer):
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
        # filter: expression*
        return arg[0] if arg else None

    @v_args(inline=True)
    def constant(self, value):
        # constant: string | number
        # Note: Do nothing!
        return value

    @v_args(inline=True)
    def value(self, value):
        # value: string | number | property
        # Note: Do nothing!
        return value

    def value_list(self, args):
        # value_list: [ OPERATOR ] value ( "," [ OPERATOR ] value )*
        values = []
        for value in args:
            try:
                value = float(value)
            except ValueError:
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
            else:
                if value.is_integer():
                    value = int(value)
            values.append(value)
        return values

    def value_zip(self, arg):
        # value_zip: [ OPERATOR ] value ":" [ OPERATOR ] value (":" [ OPERATOR ] value)*
        raise NotImplementedError

    def value_zip_list(self, arg):
        # value_zip_list: value_zip ( "," value_zip )*
        raise NotImplementedError

    def expression(self, arg):
        # expression: expression_clause ( OR expression_clause )
        # expression with and without 'OR'
        return {"or": arg} if len(arg) > 1 else arg[0]

    def expression_clause(self, arg):
        # expression_clause: expression_phrase ( AND expression_phrase )*
        # expression_clause with and without 'AND'
        return {"and": arg} if len(arg) > 1 else arg[0]

    def expression_phrase(self, arg):
        # expression_phrase: [ NOT ] ( comparison | predicate_comparison | "(" expression ")" )
        if len(arg) == 1:
            # without NOT
            return arg[0]

        # with NOT
        return {"!and": [arg[1]]}

    @v_args(inline=True)
    def comparison(self, value):
        # comparison: constant_first_comparison | property_first_comparison
        # Note: Do nothing!
        return value

    def property_first_comparison(self, arg):
        # property_first_comparison: property ( value_op_rhs | known_op_rhs | fuzzy_string_op_rhs | set_op_rhs |
        # set_zip_op_rhs )
        return {arg[0]: arg[1]}

    def constant_first_comparison(self, arg):
        # constant_first_comparison: constant value_op_rhs
        # TODO: Probably the value_op_rhs rule is not the best for implementing this.
        return {
            prop: {self.reversed_operator_map[oper]: arg[0]}
            for oper, prop in arg[1].items()
        }

    @v_args(inline=True)
    def value_op_rhs(self, operator, value):
        # value_op_rhs: OPERATOR value
        return {op_conv_map(operator.value): value}

    def known_op_rhs(self, arg):
        # known_op_rhs: IS ( KNOWN | UNKNOWN )
        if arg[1] == "KNOWN":
            key = "!=="
        if arg[1] == "UNKNOWN":
            key = "=="
        return {key: None}

    def fuzzy_string_op_rhs(self, arg):
        # fuzzy_string_op_rhs: CONTAINS string | STARTS [ WITH ] string | ENDS [ WITH ] string

        # The WITH keyword may be omitted.
        if isinstance(arg[1], Token) and arg[1].type == "WITH":
            pattern = arg[2]
        else:
            pattern = arg[1]

        if arg[0] == "CONTAINS":
            like = f"%{pattern}%"
        elif arg[0] == "STARTS":
            like = f"{pattern}%"
        elif arg[0] == "ENDS":
            like = f"%{pattern}"
        return {"like": like}

    def set_op_rhs(self, arg):
        # set_op_rhs: HAS ( [ OPERATOR ] value | ALL value_list | ANY value_list | ONLY value_list )

        if len(arg) == 2:
            # only value without OPERATOR
            return {"contains": [arg[1]]}

        if arg[1] == "ALL":
            return {"contains": arg[2]}
        if arg[1] == "ANY":
            return {"or": [{"contains": [value]} for value in arg[2]]}
        if arg[1] == "ONLY":
            raise NotImplementedError(
                '"set_op_rhs: HAS ONLY value_list" has not been implemented.'
            )

        # value with OPERATOR
        raise NotImplementedError(
            '"set_op_rhs: HAS OPERATOR value" has not been implemented.'
        )

    def set_zip_op_rhs(self, arg):
        # set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list |
        # ANY value_zip_list )
        raise NotImplementedError

    def predicate_comparison(self, arg):
        # predicate_comparison: LENGTH property OPERATOR value
        operator = arg[2].value
        if operator in self.list_operator_map:
            return {arg[1]: {self.list_operator_map[operator]: arg[3]}}
        if operator in {">=", "<="}:
            return {
                arg[1]: {
                    "or": [
                        {self.list_operator_map[operator[0]]: arg[3]},
                        {self.list_operator_map[operator[1]]: arg[3]},
                    ]
                }
            }

        raise TransformerError(
            f"length_comparison has failed with {arg}. Unknown operator."
        )

    def property_zip_addon(self, arg):
        # property_zip_addon: ":" property (":" property)*
        raise NotImplementedError

    def property(self, arg):
        # property: IDENTIFIER ( "." IDENTIFIER )*
        return ".".join(arg)

    @v_args(inline=True)
    def string(self, string):
        # string: ESCAPED_STRING
        return string.strip('"')

    def number(self, arg):
        # number: SIGNED_INT | SIGNED_FLOAT
        token = arg[0]
        if token.type == "SIGNED_INT":
            type_ = int
        elif token.type == "SIGNED_FLOAT":
            type_ = float
        return type_(token)

    def __default__(self, data, children, meta):
        raise NotImplementedError(
            f"Calling __default__, i.e., unknown grammar concept. data: {data}, children: {children}, meta: {meta}"
        )
