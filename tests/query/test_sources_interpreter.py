from lark import Lark
from mkdocs_dataview.query.solvers import SourcesInterpreter, LARK_GRAMMAR


def test(subtests):
    tests = [
        [r"""FROM #tag""", [{"type": "tag", "value": "tag"}]],
        [r"""FROM "path/other/folder" """, [{"type": "path", "value": "path/other/folder"}]],

        # TODO: implement 
        # [r"""FROM #tag1 AND #tag2""", [{"type": "tag", "value": "tag1"}, {"type": "tag", "value": "tag2"}]],
        # [r"""FROM "path1" AND "path2" """, [{"type": "path", "value": "path1"}, {"type": "path", "value": "path2"}]],
    ]

    lark = Lark(LARK_GRAMMAR, start='from_clause')
    for i, (query, expected_result) in enumerate(tests):
        with subtests.test(msg=f"Interpreter test line {i+15} {query}"):
            tree = lark.parse(query)
            sources = SourcesInterpreter().visit(tree)
            assert sources == expected_result
