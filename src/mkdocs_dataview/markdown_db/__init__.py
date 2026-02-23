"""
Module for handling markdown files.

- building an index of them
- rendering them
"""

__version__ = "0.0.0.dev"

from .file_renderer import FilePlugin

__all__ = [
    "file_renderer",
    "index",
    "md_renderer",
]
