"""
Main module for running this module as external script on mkdocs.
"""

from .markdown_db import FilePlugin

if __name__ == "__main__":
    sut = FilePlugin()
    sut.collect_data("./docs")
    sut.render_all_templates("./docs")
