"""
This module defines the LARK grammar for the dataview query language.
"""
# Quick recap for LARK grammar
#
# Without `?`:
#   The rule always creates a branch in the tree, even if it just wraps a
#   single child.
#
# With `?`:
#   If the rule matches multiple children, it creates a branch as usual. If it
#   matches only a single child, that child is returned directly, and the
#   rule's own node is skipped.


LARK_GRAMMAR = r"""
// Entry points
full_clause : view_type select_clause [from_clause] [where_clause]

view_type : CNAME

from_clause : "FROM"i from_expression
where_clause : "WHERE"i expression
select_clause : select_alias_expression ("," select_alias_expression)*

?select_alias_expression : select_expression
                         | select_expression "as"i ALIAS_NAME -> aliased_select_expression

ALIAS_NAME : STRING_CONSTANT

select_expression : sum

//////////////////////////
// FOR FROM clause
//////////////////////////

// from_expression and expression are the same, except for atoms
?from_expression : or_from_expression

?or_from_expression : and_from_expression
                     | or_from_expression "OR"i and_from_expression

?and_from_expression : not_from_expression
                      | and_from_expression "AND"i not_from_expression

?not_from_expression : from_atom
                      | "NOT"i not_from_expression

?from_atom : tag_source
            | path_source

tag_source : "#" identifier

path_source : "\"" path "\""

path : CNAME ("/" CNAME)*


//////////////////////////
// Expression hierarchy with operator precedence
//////////////////////////

?expression : or_expression

?or_expression : and_expression
               | or_expression "OR"i and_expression -> or_op

?and_expression : not_expression
                | and_expression "AND"i not_expression -> and_op

?not_expression : comparison
                | "NOT"i not_expression -> not_op

?comparison : sum
            | sum "==" sum -> eq_op
            | sum "!=" sum -> neq_op
            | sum "<" sum -> lt_op
            | sum ">" sum -> gt_op
            | sum "<=" sum -> lte_op
            | sum ">=" sum -> gte_op
            | sum "IN"i sum -> in_op
            | sum "CONTAINS"i sum -> contains_op

?sum : product
     | sum "+" product -> add_op
     | sum "-" product -> sub_op

?product : atom
         | product "*" atom -> mul_op
         | product "/" atom -> div_op

?atom : literal
      | function_call
      | "(" expression ")"
      | list
      | object
      | identifier

function_call : FUNCTION_NAME "(" [expression ("," expression)*] ")"

list : "[" [expression ("," expression)*] "]"
object : "{" [object_item ("," object_item)*] "}"
object_item : DICT_KEY ":" expression

identifier : IDENTIFIER

literal : STRING_CONSTANT
        | SIGNED_INT
        | SIGNED_FLOAT
        | BOOLEAN_TRUE
        | BOOLEAN_FALSE
        | NULL

// Terminals
BOOLEAN_TRUE : "true"i
BOOLEAN_FALSE : "false"i
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
