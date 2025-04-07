"""
Tests for mkdocs dataview plugin
"""
import io
from collections import defaultdict

import frontmatter
import mkdocs_dataview.plugin
from mkdocs_dataview.parser import (
    execute_expression_list,
    _execute_where_clause,
    execute_get_select_column_names,
)

ABC_OUT = """
|a|b|c|
|--|--|--|
"""

NESTED_PROPS_MD_FILE = """
---
cprop:
    nestedA: 1
    nestedB: 2
tags:
    - tagA
---

content
"""

def test_table_header():
    """tests for table header"""
    out = io.StringIO()
    select_list = ['a', 'b', 'c']

    mkdocs_dataview.plugin.render_table_header(select_list, out)

    assert out.getvalue() == ABC_OUT[1:]


class MockIndexBuilder(mkdocs_dataview.plugin.IndexBuilder):
    """Data View plugin main class."""
    def __init__(self):
        self.sources = {}
        self.tags = defaultdict(list)

    def add_tag(self, tag: str, metadata: dict) -> None:
        self.tags[tag].append(metadata)

    def add_file(self, file_path: str, metadata: dict) -> None:
        self.sources[file_path] = metadata


def test_nested_props_in_metadata():
    """test for nested properties in metadata"""

    data = frontmatter.loads(NESTED_PROPS_MD_FILE)
    mock_index_builder = MockIndexBuilder()
    mkdocs_dataview.plugin.build_index(
        data, "some_path/file.md", "/docs/some_path/", mock_index_builder
    )

    assert mock_index_builder.tags['tagA'] == [{
        "file": {
            "name": 'file.md',
            "path": '/docs/some_path/',
        },
        "metadata": {
            "cprop": {
                "nestedA": 1,
                "nestedB": 2,
            },
            "tags": [
                "tagA",
            ],
        }
    }]


def test_split_inline_query():
    """test inline tick splits"""

    data = [
        ("line without ticks", ["line without ticks"]),
        ("line with unclosed ` tick", ["line with unclosed ` tick"]),
        ("line with `one` tick", ["line with ", "`one`", " tick"]),
        ("line with `one` tick `and` more", ["line with ", "`one`", " tick ", "`and`", " more"]),
        ("line with `one complex` tick", ["line with ", "`one complex`", " tick"]),
    ]

    for query, expected_result in data:
        assert list(mkdocs_dataview.plugin.split_inline_query(query)) == expected_result


def test_parser_expression_list():
    """test lark grammar for expression list"""

    identifers = {
        "all": "all-on",
        "number_3": 3,
        "array_a_b_c": ['a', 'b', 'c'],
        "inner_dict": {
            "one": 1,
        }
    }

    tests = [
        (""" "some string" """,
            ['some string'],
            ['"some string"']),

        ("all, tree, identifiers",
            ['all-on', '', ''],
            ["all", "tree", "identifiers"]),

        ("number_3 + 2",
            [5],
            ["number_3+2"]),

        ("1 - 2 - 3",
            [-4],
            ["1-2-3"]),

        ("inner_dict.one + 2",
            [3],
            ["inner_dict.one+2"]),

        (""" ["a", "b", "c"] """,
            [["a", "b", "c"]],
            ['["a","b","c"]']),

        (""" ["a", "b", number_3] """,
            [["a", "b", 3]],
            ['["a","b",number_3]']),

        (""" sum(number_3, 2) """,
            [5],
            ["sum(number_3, 2)"]),

        (""" econtains(array_a_b_c, "b") """,
            [True],
            ["""econtains(array_a_b_c, "b")"""]),

        (""" econtains(array_a_b_c, "bb") """,
            [False],
            ["""econtains(array_a_b_c, "bb")"""]),

        (""" "one", "two" as "second" """,
            ['one', 'two'],
            ['"one"', 'second']),
    ]

    for query, expected_result, column_names in tests:
        assert execute_expression_list(query, identifers) == expected_result
        assert execute_get_select_column_names(query) == column_names


def test_parser_expression_aritchmetic_priority():
    """test lark grammar for expression list"""

    tests = [
        ('1',            1),
        ('1 + 2',        3),
        ('1 + 2 - 3',    0),
        ('3 - 2 * 3',   -3),
        ('(3 - 2) * 3',  3),
        ('3 * (3 - 2)',  3),
        ('(3 * 3) - 2',  7),
        ('(3 * 3) * 2',  18),

        ('1 != 3',        True),

        ('2 != 2',        False),
        ('"a" != "b"',        True),
        ('"a" != "a"',        False),
        ('"a" != "A"',        True),

        ('3 >= 3',        True),
        ('3 >= 1',        True),
        ('3 >= -4',        True),
        ('3 >= 4',        False),

        ('3 > 3',        False),
        ('3 > 1',        True),
        ('3 > -4',        True),
        ('3 > 4',        False),

        ('3 <= 3',        True),
        ('3 <= 1',        False),
        ('3 <= -4',        False),
        ('3 <= 4',        True),

        ('3 < 3',        False),
        ('3 < 1',        False),
        ('3 < -4',        False),
        ('3 < 4',        True),

        ('NOT True',        False),
        ('NOT False',        True),
        ('NOT 1',        False),
        ('NOT 0',        True),

        ('true AND True',        True),
        ('3 < 4 AND True',        True),
        ('3 < 4 AND False',        False),
        ('4 < 4 AND True',        False),

        ('True AND 3 < 4 ',        True),
        ('False AND 3 < 4',        False),
        ('True AND 4 < 4',        False),

        ('True AND False OR True',        True),
        ('True OR False AND True',        True),
        ('False OR True AND False',        False),

        ('True AND False OR False',   False),

        ('False OR 0',        False),
        ('False OR 0 + 1',        True),


        ('3 * (3 - 2) == 3',        True),
        ('3 * (3 - 2) == (1 + 2)',  True),

        ('1 IN [1, 2, 3]',  True),
        ('0 IN [1, 2, 3]',  False),
        ('NOT 1 IN [1, 2, 3]',  False),
        ('NOT 0 IN [1, 2, 3]',  True),

        ('[1, 2, 3] CONTAINS 1',  True),
        ('[1, 2, 3] CONTAINS 0',  False),
        ('NOT [1, 2, 3] CONTAINS 1',  False),
        ('NOT [1, 2, 3] CONTAINS 0',  True),

        ('sum(1)',  1),
        ('sum(1, 2)',  3),
    ]

    for query, expected_result in tests:
        result = execute_expression_list(query, {})[0]
        assert result == expected_result
        assert type(result) == type(expected_result)  # pylint: disable=unidiomatic-typecheck


def test_parser_expression_objects():
    """test lark grammar for expression list"""

    tests = [
        ('{ key: 1 }',  {"key": 1}),
        ('{ key: { inner: 2 } }',  {"key": { "inner": 2}}),
    ]

    for query, expected_result in tests:
        result = execute_expression_list(query, {})[0]
        assert result == expected_result

# pylint: disable=line-too-long
def test_parser_where_clause():
    """test lark grammar for expression list"""

    identifers = {
        "all": "all-on",
        "number_3": 3,
        "array_a_b_c": ['a', 'b', 'c'],
        "value_b": 'b',

        'this': {
            'metadata': {
                'featureID': 'special_tag',
            },
        },
        'metadata': {
            'tags': [
                "special_tag"
            ]
        },
        'file': {
            'path': './docs/index.md',
            'name': 'index.md',
            'link': '[index.md](../../index.md)'
        },
    }

    tests = [
        (""" WHERE 1""", [1]),
        (""" WHERE 1 AND 1""", [True]),
        (""" WHERE 1 AND 0""", [False]),
        (""" WHERE 1 OR 0""", [True]),
        (""" WHERE (1 AND 0) AND 1""", [False]),
        (""" WHERE "a" IN ["a", "b", "c"] """, [True]),
        (""" WHERE `value_b` IN array_a_b_c """, [True]),
        ('WHERE  `metadata.featureID` != null and `metadata.featureID` != "" and this.metadata.featureID in `metadata.tags` and this.metadata.featureID != featureID', [False]),
        ('WHERE `metadata.featureID` != null and `metadata.featureID` != ""', [False]),
        ('WHERE (`metadata.featureID` == null OR `metadata.featureID` == "") and this.metadata.featureID in `metadata.tags`', [True]),
    ]

    for query, expected_result in tests:
        assert _execute_where_clause(query, identifers) == expected_result
