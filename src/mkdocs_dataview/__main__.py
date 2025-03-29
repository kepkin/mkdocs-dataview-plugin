"""
Main module for running this module as external script on mkdocs.
"""

from .plugin import DataViewPlugin

if __name__ == "__main__":
    sut = DataViewPlugin()
    sut.collect_data("./docs")
    sut.render_all_templates("./docs")