# pylint: disable=wildcard-import, method-hidden, missing-function-docstring, missing-module-docstring, protected-access
import sys
from mkdocs_dataview.query.solvers import ExpressionSolverService


def get_linenumber():
    return sys._getframe().f_back.f_lineno


def test(subtests):
    identifiers = {
        "all": "<all-value>",
        "number_3": 3,
        "array_a_b_c": ['a', 'b', 'c'],
        "inner_dict": {
            "one": 1,
        },
        "metadata": {
            "a": 1,
            "b": 2,
            "c": 10,
        }
    }

    tests = [
        [
            get_linenumber(),
            r"""1+1""",
            2,
        ],[
            get_linenumber(),
            r"""metadata.a + metadata.b > 10""",
            False,
        ],[
            get_linenumber(),
            r"""metadata.a + metadata.c > 10""",
            True,
        ],[
            get_linenumber(),
            """ "some string" """,
            'some string',
        ],[
            get_linenumber(),
            "number_3 + 2",
            5,
        ],[
            get_linenumber(),
            "1 - 2 - 3",
            -4,
        ],[
            get_linenumber(),
            "inner_dict.one + 2",
            3,
        ],[
            get_linenumber(),
            """ ["a", "b", "c"] """,
            ["a", "b", "c"],
        ],[
            get_linenumber(),
            """ ["a", "b", number_3] """,
            ["a", "b", 3],
        ],[
            get_linenumber(),
            """ sum(number_3, 2) """,
            5,
        ],[
            get_linenumber(),
            """ econtains(array_a_b_c, "b") """,
            True,
        ],[
            get_linenumber(),
            """ econtains(array_a_b_c, "bb") """,
            False,
        ]
    ]

    for line_number, query, expected_result in tests:
        with subtests.test(msg=f"Interpreter test line [{line_number}]: `{query}`"):
            res = ExpressionSolverService(query).solve(identifiers)
            assert expected_result == res
