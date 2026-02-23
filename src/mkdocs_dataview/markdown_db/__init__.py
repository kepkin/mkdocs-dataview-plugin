"""
Module for handling markdown files.

- building an index of them
- rendering them
"""

__version__ = "0.0.0.dev"

from .file_renderer import FilePlugin
from .index import IndexBuilder, build_index
from .md_renderer import RendererWithContext, render_table_header, split_inline_query

__all__ = [
    "file_renderer",
    "index",
    "md_renderer",
]
