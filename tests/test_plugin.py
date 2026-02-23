# pylint: disable=wildcard-import, method-hidden, missing-function-docstring, missing-module-docstring, protected-access
import io
from collections import defaultdict

import frontmatter
import mkdocs_dataview.plugin
import mkdocs_dataview.markdown_db

from mkdocs_dataview.markdown_db import render_table_header, split_inline_query


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

    render_table_header(select_list, out)

    assert out.getvalue() == ABC_OUT[1:]


class MockIndexBuilder(mkdocs_dataview.markdown_db.IndexBuilder):
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
    mkdocs_dataview.markdown_db.build_index(
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
        assert list(split_inline_query(query)) == expected_result
