"""
Contains solvers that used for where and expression lists
"""

from lark import Transformer, Token


def lookup_value_in_dict(data, key):
    """Get value from dict by path in key.

    Parameters:
        data: dict
        key: str like "key.inner_key.and_other_key"

    Returns None if there is no such key.
    """
    lookup_value = data

    for k in key.split('.'):
        lookup_value = lookup_value.get(k)
        if lookup_value is None:
            break

    return lookup_value


def dataview_sum(*args) -> tuple[str, int]:
    """Sum function for dataview queries"""
    return "SIGNED_INT", sum(args)


def dataview_econtains(data, value) -> tuple[str, bool]:
    """econtain function for dataview queries"""
    return "BOOLEAN", value in data


# pylint: disable=missing-function-docstring,invalid-name,broad-exception-raised,too-many-public-methods
class SolveAliasListTransformation(Transformer):
    """Transforms lark tree into list of column names"""

    def alias_expression(self, toks):
        if len(toks) == 2:
            return toks[1]
        return toks[0].update(type="ALIAS_NAME")

    def ALIAS_NAME(self, toks):
        return toks.update(value=toks.value[1:-1])

    def BIN_OP(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def SET_OP(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def CONTAINS_OP(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def IDENTIFIER(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def STRING_CONSTANT(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def not_expression(self, toks):
        return Token("STRING_CONSTANT", value="NOT " + toks[1].value)

    def add_expression(self, toks):
        return Token("STRING_CONSTANT", value=toks[0].value + toks[1].value + toks[2].value)

    def and_expression(self, toks):
        return Token("STRING_CONSTANT", value=toks[0].value + toks[1].value + toks[2].value)

    def eq_expression(self, toks):
        return Token("STRING_CONSTANT", value=toks[0].value + toks[1].value + toks[2].value)

    def or_expression(self, toks):
        return Token("STRING_CONSTANT", value=toks[0].value + toks[1].value + toks[2].value)

    def mul_expression(self, toks):
        return Token("STRING_CONSTANT", value=toks[0].value + toks[1].value + toks[2].value)

    def in_expression(self, toks):
        return Token("STRING_CONSTANT", value=toks[0].value + toks[1].value + toks[2].value)

    def contains_expression(self, toks):
        return Token("STRING_CONSTANT", value=toks[0].value + toks[1].value + toks[2].value)

    def BOOLEAN_TRUE(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def BOOLEAN_FALSE(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def NULL(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def SIGNED_INT(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def SIGNED_FLOAT(self, tok):
        return tok.update(type="STRING_CONSTANT")

    def term_list(self, toks):
        return Token("STRING_CONSTANT", value="[" + ",".join(toks) + "]")

    def term_object(self, toks):
        v = {}
        v[toks[0].value] = toks[1].value
        return toks.update(type="STRING_CONSTANT", value=repr(v))

    def function_call(self, toks):
        args = []
        for t in toks[1:]:
            if t.type != 'STRING_CONSTANT':
                raise Exception("Expect only string CONSTANTS")
            args.append(t.value)

        return Token("STRING_CONSTANT", toks[0].value + "(" + ", ".join(args) + ")")

# pylint: disable=missing-function-docstring,invalid-name,broad-exception-raised
class SolveTransformation(Transformer):
    """Transforms lark tree into list with identifiers replace by their values"""

    def __init__(self, identifiers):
        super().__init__()

        self.__identifiers=identifiers
        self.funcs = {
            "sum": dataview_sum,
            "econtains": dataview_econtains,
        }

    def BIN_OP(self, tok):
        "remove quotes from string"
        return tok.update(value=tok.value.upper())

    def SET_OP(self, tok):
        "remove quotes from string"
        return tok.update(value=tok.value.upper())

    def CONTAINS_OP(self, tok):
        "remove quotes from string"
        return tok.update(value=tok.value.upper())

    def ALIAS_NAME(self, _):
        "ingore alias names here"
        return None

    def IDENTIFIER(self, tok):
        if tok.value[0] == '`':
            tok = tok.update(value=tok.value[1:-1])

        v = lookup_value_in_dict(self.__identifiers, tok.value)

        map_python_type_to_grammar_type = {
            'int': 'SIGNED_INT',
            'str': 'STRING_CONSTANT',
            'NoneType': 'NULL',
            'list': 'LIST',
            'bool': 'BOOLEAN',
            'dict': 'OBJECT',
        }
        type_name = type(v).__name__
        if type_name not in map_python_type_to_grammar_type:
            raise Exception(f"unsupporte type for resolve {type_name}")


        if v is None:
            v = ''
        return tok.update(type=map_python_type_to_grammar_type[type_name], value=v)

    def STRING_CONSTANT(self, tok):
        "remove quotes from string"
        return tok.update(value=tok.value[1:-1])

    def not_expression(self, toks):
        v_tok = toks[1]
        if v_tok.type not in ["BOOLEAN", "SIGNED_INT"]:
            raise Exception(f"you can't use NOT operand on type `{v_tok.type}`")

        return Token("BOOLEAN", not toks[1].value)

    def add_expression(self, toks):
        return self._bin_expression(toks)

    def and_expression(self, toks):
        return self._bin_expression(toks)

    def eq_expression(self, toks):
        return self._bin_expression(toks)

    def or_expression(self, toks):
        return self._bin_expression(toks)

    def mul_expression(self, toks):
        return self._bin_expression(toks)

    def in_expression(self, toks):
        return self._bin_expression(toks)

    def contains_expression(self, toks):
        return self._bin_expression(toks)

    def BOOLEAN_TRUE(self, tok):
        "Convert to boolean"
        return tok.update(type="BOOLEAN", value=True)

    def BOOLEAN_FALSE(self, tok):
        "Convert to boolean"
        return tok.update(type="BOOLEAN", value=False)

    def NULL(self, tok):
        "Convert to None"
        return tok.update(value=None)

    def SIGNED_INT(self, tok):
        "Convert to signed number"
        return tok.update(value=int(tok))

    def SIGNED_FLOAT(self, tok):
        "Convert to signed number"
        (tok,) = tok
        return tok.update(value=float(tok))

    def term_list(self, toks):
        v = []
        for t in toks:
            v.append(self._resolve(t).value)

        return Token("LIST", v)

    def term_object(self, toks):
        v = {}
        v[toks[0].value] = toks[1].value
        return Token("OBJECT", v)

    def function_call(self, toks):
        func_token = toks[0]
        args = []
        for t in toks[1:]:
            resolved_token = self._resolve(t)
            args.append(resolved_token.value)

        new_type, new_value = self.funcs[func_token.value](*args)
        return Token(new_type, new_value)

    # pylint: disable=too-many-branches
    def _bin_expression(self, toks):
        if len(toks) == 1:
            # reduce
            return toks[0]

        if len(toks) != 3:
            raise Exception("Unsupported number of operations for mul operations", toks)

        l_op, op, r_op = toks
        new_value = None
        new_type = l_op.type
        op_value = op.value.lower()
        if op_value == '*':
            new_value = l_op.value * r_op.value
        elif op_value == '/':
            new_value = l_op.value / r_op.value
        elif op_value == '+':
            new_value = l_op.value + r_op.value
        elif op_value == '-':
            new_value = l_op.value - r_op.value
        elif op_value == 'and':
            new_type = "BOOLEAN"
            new_value = bool(l_op.value and r_op.value)
        elif op_value == 'or':
            new_type = "BOOLEAN"
            new_value = bool(l_op.value or r_op.value)
        elif op_value == '==':
            new_type = "BOOLEAN"
            new_value = l_op.value == r_op.value
        elif op_value == '!=':
            new_type = "BOOLEAN"
            new_value = l_op.value != r_op.value
        elif op_value == '<':
            new_type = "BOOLEAN"
            new_value = l_op.value < r_op.value
        elif op_value == '<=':
            new_type = "BOOLEAN"
            new_value = l_op.value <= r_op.value
        elif op_value == '>':
            new_type = "BOOLEAN"
            new_value = l_op.value > r_op.value
        elif op_value == '>=':
            new_type = "BOOLEAN"
            new_value = l_op.value >= r_op.value
        elif op_value == 'in':
            new_type = "BOOLEAN"
            new_value = l_op.value in r_op.value
        elif op_value == 'contains':
            new_type = "BOOLEAN"
            new_value = r_op.value in l_op.value
        else:
            raise Exception("Unsupported binary operations", op_value)

        return toks[0].update(type=new_type, value=new_value)

    def _resolve_identifier(self, tok):
        v = lookup_value_in_dict(self.__identifiers, tok.value)

        map_python_type_to_grammar_type = {
            "int": "SIGNED_INT",
            "str": "STRING_CONSTANT",
            "NoneType": "NULL",
            "list": "LIST",
            "bool": "BOOLEAN",
            "dict": "OBJECT",
        }
        type_name = type(v).__name__
        if type_name not in map_python_type_to_grammar_type:
            raise Exception(f"unsupporte type for resolve `{type_name}`")

        if v is None:
            v = ''
        return tok.update(type=map_python_type_to_grammar_type[type_name], value=v)

    def _resolve(self, tok):
        if isinstance(tok, Token):
            if tok.type in [
                "SIGNED_INT",
                "SIGNED_FLOAT",
                "BOOLEAN",
                "STRING_CONSTANT",
                "NULL",
                "LIST"]:
                return tok

            if tok.type == "IDENTIFIER":
                return self._resolve_identifier(tok)

            raise Exception(f"unsupporte type for resolve `{tok.type}`")

        # maybe this code is not needed
        v = [self._resolve(i).value for i in tok.scan_values(lambda v: isinstance(v, Token))]
        return Token("LIST", v)
