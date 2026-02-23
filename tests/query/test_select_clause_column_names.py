from lark import Lark
from mkdocs_dataview.query.solvers import SelectClauseColumnNamesTransformer, LARK_GRAMMAR
import sys

def get_linenumber():
  return sys._getframe().f_back.f_lineno

def test_column_names(subtests):
    tests = [
        [
            get_linenumber(),
            r"""metadata.featureID as "featureID", file.link, metadata.a + metadata.b""", 
            ['featureID', 'file.link', 'metadata.a + metadata.b'],
        ],
        [
            get_linenumber(),
            r"""1 + 1""", 
            ['1 + 1'],
        ],
        [
            get_linenumber(),
            r"""file.link""", 
            ['file.link'],
        ]
    ]

    lark = Lark(LARK_GRAMMAR, start='select_clause')
    for _, (line_number, query, expected_result) in enumerate(tests):
        with subtests.test(msg=f"Parse column names test line [{line_number}] `{query}`"):
            tree = lark.parse(query)
            sources = SelectClauseColumnNamesTransformer().visit(tree)
            assert sources == expected_result
