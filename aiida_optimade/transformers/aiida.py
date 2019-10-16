from lark import Transformer

op_expr = {"<": "$lt", "<=": "$lte", ">": "$gt", ">=": "$gte", "!=": "$ne", "=": "$eq"}

# Conversion map from the OPTiMaDe operators to the QueryBuilder operators
op_conv_map = {
    "=": "==",
    "!=": "!==",
    # '=in=': 'in',
    # '=notin=': '!in',
    ">": ">",
    "<": "<",
    ">=": ">=",
    "<=": "<=",
    # '=like=': 'like',
    # '=ilike=': 'ilike'
}


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


class AiidaTransformer(Transformer):
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

        op = op_conv_map[args[1].value]
        value_token = args[2]
        try:
            value = float(value_token.value)
        except ValueError:
            value = value_token.value
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
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
            elements.append(value)
        return elements
