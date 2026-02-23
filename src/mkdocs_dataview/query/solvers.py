"""
Contains solvers that used for where and expression lists
"""

from lark import Transformer, Lark
from lark.visitors import Interpreter
from .grammar import LARK_GRAMMAR


class QueryError(Exception):
    pass


class FuncitonCallError(QueryError, NameError):
    pass


class TransformationError(QueryError):
    pass



class QueryService():
    def __init__(self, query):
        self.query = query
        self.lark = Lark(LARK_GRAMMAR, start='full_clause')
        self.tree = self.lark.parse(query)
        parsed_data = FullClauseInterpreter().visit(self.tree)
        self.data = {}

        # @TODO: maybe it's easier to rewrite using Tree.find_smt?
        for v in parsed_data:
            if v is None:
                # @TODO: it must be optional "from_clause" or where_clause??
                continue
            self.data[v["type"]] = None
            if "value" in v:
                self.data[v["type"]] = v["value"]

    def get_render_type(self):
        return self.data["view_type"]

    def get_sources(self):
        if self.data.get("from_clause"):
            return SourcesInterpreter().visit(self.data["from_clause"])

        return []

    def columns(self):
        return SelectClauseColumnNamesTransformer().visit(self.data["select_clause"])

    def render_columns(self, identifiers):
        return ExpressionSolver(identifiers).transform(self.data["select_clause"])

    def get_where_expression(self):
        if self.data.get("where_clause"):
            return self.data["where_clause"].pretty()

        return ""

    def where(self, identifiers):
        if self.data.get("where_clause"):
            return ExpressionSolver(identifiers).transform(self.data["where_clause"])

        return True


class FullClauseInterpreter(Interpreter):
    """
    Interpreter that returns list of query parts.

    Example output:

        [
            {
                "type": "view_type",
                "value": "TABLE",
            },
            {
                "type": "select_clause",
                "value": ['featureID', 'file.link', 'metadata.a + metadata.b'],
            },
            {
                "type": "from_clause",
                "value": [{'type': 'tag', 'value': 'tag'}],
            },
        ]

    Example usage:

    sources = FullClauseInterpreter().visit(tree)




    """
    def tag_source(self, tree):
        # tag_source : "#" identifier
        # identifier is a child
        # We need to get the value of identifier
        # identifier returns a string in SolveTransformation, but here we are
        # visiting the tree
        # tree.children[0] is the identifier node (or token if it was a
        # terminal, but identifier is a rule)
        # Wait, identifier rule: identifier : IDENTIFIER
        # So tree.children[0] is a Token or a Tree?
        # In parser.py: identifier : IDENTIFIER
        # So it's a rule.

        # Let's look at the tree structure.
        # tag_source -> identifier -> IDENTIFIER token

        # We can just extract the text from the identifier subtree
        # Or simpler: just get the text of the whole tag_source node
        # But we want the tag name.

        # Let's traverse down to identifier
        identifier_node = tree.children[0]
        # identifier node has one child: the token
        tag_name = identifier_node.children[0].value
        # Remove backticks if present (handled in identifier rule usually but
        # here we access token directly)
        if tag_name.startswith('`'):
            tag_name = tag_name[1:-1]

        return {'type': 'tag', 'value': tag_name}

    def view_type(self, tree):
        return {'type': 'view_type', 'value': tree.children[0].value}

    def select_clause(self, tree):
        return {'type': 'select_clause', 'value': tree}

    def from_clause(self, tree):
        return {'type': 'from_clause', 'value': tree}

    def where_clause(self, tree):
        return {'type': 'where_clause', 'value': tree}


class SelectClauseColumnNamesTransformer(Interpreter):

    def aliased_select_expression(self, tree):
        v = self.visit_children(tree)
        return v[1].value[1:-1]

    def select_expression(self, tree):
        v = self.visit_children(tree)
        vv = []
        for i in v:
            for ii in i:
                vv.append(ii)
        v = ''.join([str(i) for i in vv])
        return v

    def add_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " + " + v[1]

    def identifier(self, tree):
        v = self.visit_children(tree)
        return v[0].value

    def literal(self, tree):
        v = self.visit_children(tree)
        return v[0].value

    def sub_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " - " + v[1]

    def mul_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + "  * " + v[1]

    def div_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " / " + v[1]

    def and_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " AND " + v[1]

    def or_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " OR " + v[1]

    def eq_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + "  == " + v[1]

    def neq_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " + != " + v[1]

    def lt_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " < " + v[1]

    def gt_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " > " + v[1]

    def lte_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " <= " + v[1]

    def gte_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " >= " + v[1]

    def in_op(self, tree):
        v = self.visit_children(tree)
        return v[0] + " in " + v[1]

    def contains_op(self, tree):
        v = self.visit_children(tree)
        return v[1] + " in " + v[0]

    def not_op(self, tree):
        v = self.visit_children(tree)
        return "not " + v[0]


class SourcesInterpreter(Interpreter):
    """
    Interpreter that collects all sources from the FROM clause.

    Example usage:

    sources = SourcesInterpreter().visit(tree)
    """
    def tag_source(self, tree):
        # tag_source : "#" identifier
        # identifier is a child
        # We need to get the value of identifier
        # identifier returns a string in SolveTransformation, but here we are
        # visiting the tree
        # tree.children[0] is the identifier node (or token if it was a
        # terminal, but identifier is a rule)
        # Wait, identifier rule: identifier : IDENTIFIER
        # So tree.children[0] is a Token or a Tree?
        # In parser.py: identifier : IDENTIFIER
        # So it's a rule.

        # Let's look at the tree structure.
        # tag_source -> identifier -> IDENTIFIER token

        # We can just extract the text from the identifier subtree
        # Or simpler: just get the text of the whole tag_source node
        # But we want the tag name.

        # Let's traverse down to identifier
        identifier_node = tree.children[0]
        # identifier node has one child: the token
        tag_name = identifier_node.children[0].value
        # Remove backticks if present (handled in identifier rule usually but
        # here we access token directly)
        if tag_name.startswith('`'):
            tag_name = tag_name[1:-1]

        return {'type': 'tag', 'value': tag_name}

    def path_source(self, tree):
        # path_source : "\"" path "\""
        # path is a rule: path : CNAME ("/" CNAME)*
        # We want the full path string.
        # We can reconstruct it from children of path node.

        path_node = tree.children[0]
        path_parts = [t.value for t in path_node.children]
        path_value = "/".join(path_parts)

        return {'type': 'path', 'value': path_value}

    def from_clause(self, tree):
        return self.visit_children(tree)

    def from_expression(self, tree):
        return self.visit_children(tree)

    def or_from_expression(self, tree):
        return self.visit_children(tree)

    def and_from_expression(self, tree):
        return self.visit_children(tree)

    def not_from_expression(self, tree):
        return self.visit_children(tree)

    def from_atom(self, tree):
        return self.visit_children(tree)


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


def dataview_length(value) -> tuple[str, int]:
    """length function"""
    if value is None:
        return "SIGNED_INT", 0
    return "SIGNED_INT", len(value)


def dataview_date(value) -> tuple[str, str]:
    """date function (simplified, just returns string for now)"""
    # In a real implementation, this would parse date strings
    return "STRING_CONSTANT", str(value)


def dataview_link(path, display=None) -> tuple[str, str]:
    """link function"""
    if display:
        return "STRING_CONSTANT", f"[{display}]({path})"
    return "STRING_CONSTANT", f"[{path}]({path})"


def dataview_choice(condition, if_true, if_false) -> tuple[str, any]:
    """choice function"""
    if condition:
        return "STRING_CONSTANT", if_true  # Type might vary, but simplifying
    return "STRING_CONSTANT", if_false


def dataview_default(value, default_val) -> tuple[str, any]:
    """default function"""
    if value is None or value == "null":
        return "STRING_CONSTANT", default_val
    return "STRING_CONSTANT", value


# pylint: disable=too-few-public-methods
class ExpressionSolverService():
    def __init__(self, expression):
        lark = Lark(LARK_GRAMMAR, start='expression')
        try:
            self.tree = lark.parse(expression)
        except:
            print("Tryied to parse where expresion", expression)
            raise

    def solve(self, identifiers=None):
        return ExpressionSolver(identifiers).transform(self.tree)


# pylint: disable=too-many-public-methods
class ExpressionSolver(Transformer):
    """
    This class is not intended to be used directly. Use ExpersionSolverService instead.
    Solves the expression grammar tree by reducing complex terms into simple ones.

    Example:
            tree = lark.parse("a + 2")


            res_transform = ExpressionSolver({"a": 1}).transform(tree)
            res_transform should be 3


    """

    def __init__(self, identifiers):
        super().__init__()
        self.__identifiers = identifiers
        self.funcs = {
            "sum": dataview_sum,
            "econtains": dataview_econtains,
            "length": dataview_length,
            "date": dataview_date,
            "link": dataview_link,
            "choice": dataview_choice,
            "default": dataview_default,
        }

    def select_clause(self, toks):
        return toks

    def where_clause(self, toks):
        if len(toks) != 1:
            raise TransformationError("unexpected where tokens size")

        return toks[0]

    def aliased_select_expression(self, toks):
        return toks[0]

    def select_expression(self, toks):
        return toks[0]

    def identifier(self, toks):
        """resolves identifiers to their values"""
        tok = toks[0]
        if tok.value[0] == '`':
            tok = tok.update(value=tok.value[1:-1])

        v = lookup_value_in_dict(self.__identifiers, tok.value)

        if v is None:
            v = ''
        return v

    # pylint: disable=too-many-return-statements
    def literal(self, toks):
        tok = toks[0]
        if tok.type == 'STRING_CONSTANT':
            return tok.value[1:-1]
        if tok.type == 'SIGNED_INT':
            return int(tok)
        if tok.type == 'SIGNED_FLOAT':
            return float(tok)
        if tok.type == 'BOOLEAN_TRUE':
            return True
        if tok.type == 'BOOLEAN_FALSE':
            return False
        if tok.type == 'NULL':
            return None
        return tok.value

    def add_op(self, toks):
        return toks[0] + toks[1]

    def sub_op(self, toks):
        return toks[0] - toks[1]

    def mul_op(self, toks):
        return toks[0] * toks[1]

    def div_op(self, toks):
        return toks[0] / toks[1]

    def and_op(self, toks):
        return bool(toks[0] and toks[1])

    def or_op(self, toks):
        return bool(toks[0] or toks[1])

    def eq_op(self, toks):
        return toks[0] == toks[1]

    def neq_op(self, toks):
        return toks[0] != toks[1]

    def lt_op(self, toks):
        return toks[0] < toks[1]

    def gt_op(self, toks):
        return toks[0] > toks[1]

    def lte_op(self, toks):
        return toks[0] <= toks[1]

    def gte_op(self, toks):
        return toks[0] >= toks[1]

    def in_op(self, toks):
        return toks[0] in toks[1]

    def contains_op(self, toks):
        return toks[1] in toks[0]

    def not_op(self, toks):
        return not toks[0]

    def list(self, toks):
        return toks

    def object(self, toks):
        return dict(toks)

    def object_item(self, toks):
        return (toks[0].value, toks[1])

    def function_call(self, toks):
        func_token = toks[0]
        args = toks[1:]

        if func_token.value not in self.funcs:
            raise FuncitonCallError("Unknown function", name = func_token.value)

        _, new_value = self.funcs[func_token.value](*args)
        # We return just the value now, as the transformer seems to expect values
        return new_value
