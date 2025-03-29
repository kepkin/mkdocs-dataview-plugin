"""
Tests for mkdocs dataview plugin
"""
import io

import mkdocs_dataview.plugin

ABC_OUT = """
|a|b|c|
|--|--|--|
"""


def test_table_header():
    """tests for table header"""
    out = io.StringIO()
    select_list = ['a', 'b', 'c']

    mkdocs_dataview.plugin.render_table_header(select_list, out)

    assert out.getvalue() == ABC_OUT[1:]
