"""
Tests for mkdocs dataview plugin
"""
import io
from collections import defaultdict

import frontmatter
import mkdocs_dataview.plugin

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


# pylint: disable=line-too-long
def test_split_token():
    """test token splits"""

    data = [
        ("'one'", ["'one'"]),
        (" 'one'", ["'one'"]),
        (" 'one' ", ["'one'"]),
        (" 'one' == 'one' ", ["'one'", "==", "'one'"]),
        (" this.variable != 12 ", ["this.variable", "!=", "12"]),
        ('`metadata.featureID` != null and `metadata.featureID` != ""\n', ['`metadata.featureID`', '!=', 'null', 'and', '`metadata.featureID`', '!=', '""']),
    ]

    for query, expected_result in data:
        assert list(mkdocs_dataview.plugin.split_token(query)) == expected_result
