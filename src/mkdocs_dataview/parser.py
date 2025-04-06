"""
This is a ebnf parser for dataview grammar
"""

from lark import Lark, Token
from .solvers import SolveAliasListTransformation, SolveTransformation

LARK_GRAMMAR=r"""

select_expression : alias_expression ("," alias_expression)*

alias_expression : expression
                 | expression "as"i ALIAS_NAME

ALIAS_NAME : STRING_CONSTANT

where_clause : "WHERE"i expression

expression_list : expression ["," expression_list]

?expression : or_expression

?or_expression : or_expression [BOOLEAN_OR or_expression]
               | and_expression

?and_expression : and_expression [BOOLEAN_AND and_expression]
                | eq_expression

?eq_expression : eq_expression [ EQUALITY_OP eq_expression ]
               | add_expression

?add_expression : add_expression [ ADD_OP mul_expression ]
                | mul_expression

?mul_expression : mul_expression [ MUL_OP mul_expression ]
                | term

?term : term_item
       | term_list
       | term_object
       | function_call
       | in_expression
       | contains_expression
       | not_expression
       | "(" expression ")"

term_list : "[" "]"
          | "[" term_item ("," term_item)* "]"

term_object : "{" "}"
            | "{" DICT_KEY ":" term_object_value "}"

?term_object_value : term_item
                  | term_object

not_expression : NOT_OP term_item
               | NOT_OP in_expression
               | NOT_OP contains_expression
            #    | NOT_OP BOOLEAN_TRUE
            #    | NOT_OP BOOLEAN_FALSE
            #    | NOT_OP eq

in_expression : term_item SET_OP term_list
              | IDENTIFIER SET_OP IDENTIFIER
              | term_item SET_OP IDENTIFIER

contains_expression : term_list CONTAINS_OP term_item
              | IDENTIFIER CONTAINS_OP IDENTIFIER
              | IDENTIFIER CONTAINS_OP term_item

function_call : FUNCTION_NAME "(" term_item ("," term_item)* ")"

?term_item : BOOLEAN_FALSE
     | BOOLEAN_TRUE
     | NULL
     | STRING_CONSTANT
     | SIGNED_INT
     | SIGNED_FLOAT
     | IDENTIFIER

BOOLEAN_TRUE : "true"i
BOOLEAN_FALSE : "false"i


NOT_OP : "NOT"i
BOOLEAN_AND : "AND"i
BOOLEAN_OR : "OR"i
MUL_OP : "*" | "/"
ADD_OP : "+" | "-"
EQUALITY_OP : "<" | ">" | "==" | "!=" | ">=" | "<="
SET_OP : "IN"i
CONTAINS_OP : "CONTAINS"i

NULL : "null"i

STRING_CONSTANT : ESCAPED_STRING
FUNCTION_NAME : CNAME | CNAME ("." CNAME)*
DICT_KEY : CNAME
IDENTIFIER : "`" CNAME ("." CNAME)* "`" | CNAME ("." CNAME)*


%import common.CNAME
%import common.ESCAPED_STRING
%import common.SIGNED_FLOAT
%import common.SIGNED_INT
%import common.WS
%ignore WS
"""


_dataview_where_clause = Lark(LARK_GRAMMAR, start='where_clause')
_dataview_select_expression = Lark(LARK_GRAMMAR, start='select_expression')


def execute_expression_list(expression_list, identifiers):
    "Returns list of solved or simplified expressions"
    tree = _dataview_select_expression.parse(expression_list)
    resolved_tree = SolveTransformation(identifiers).transform(tree)
    return [i.value for i in resolved_tree.scan_values(lambda v: isinstance(v, Token))]


def _execute_where_clause(query, identifiers):
    tree = _dataview_where_clause.parse(query)
    resolved_tree = SolveTransformation(identifiers).transform(tree)
    return [i.value for i in resolved_tree.scan_values(lambda v: isinstance(v, Token))]


def execute_where_clause(query, identifiers):
    "Returns either TRUE or FALSE for WHERE clause"
    return bool(_execute_where_clause(query, identifiers)[0])


def execute_get_select_column_names(query):
    "Returns list of column names from expliression list"
    tree = _dataview_select_expression.parse(query)
    resolved_tree = SolveAliasListTransformation().transform(tree)
    r = [i.value for i in resolved_tree.scan_values(lambda v: isinstance(v, Token))]
    return r
