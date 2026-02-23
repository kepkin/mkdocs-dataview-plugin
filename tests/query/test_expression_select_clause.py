# pylint: disable=wildcard-import, method-hidden, missing-function-docstring, missing-module-docstring, protected-access
import sys

from lark import Lark
from mkdocs_dataview.query.solvers import ExpressionSolver, LARK_GRAMMAR


def get_linenumber():
    return sys._getframe().f_back.f_lineno


def test_select_expression_values_transformer(subtests):
    tests = [
        [
            get_linenumber(),
            r"""metadata.featureID as "featureID", file.link, metadata.a + metadata.b""",
            {
                "metadata": {
                    "featureID": "<feature-ID-value>",
                    "a": 1,
                    "b": 1,
                },
                "file": {
                    "link": "<file-link-value>",
                },
            },
            ['<feature-ID-value>', '<file-link-value>', 2],
        ],
        [
            get_linenumber(),
            r"""1 + 1""",
            {},
            [2],
        ]
    ]

    lark = Lark(LARK_GRAMMAR, start='select_clause')
    for _, (line_number, query, identifiers, expected_result) in enumerate(tests):
        with subtests.test(msg=f"Solve column values test line [{line_number}] `{query}`"):
            tree = lark.parse(query)
            sources = ExpressionSolver(identifiers).transform(tree)
            assert sources == expected_result
