"""
This module allows to render 'dataview' fences based on collected data in metadata in .md files.
"""

from collections import defaultdict
import io
import os
import shutil

import frontmatter

from mkdocs.config import base
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files, File
from mkdocs.structure.pages import Page

from .markdown_db.md_renderer import RendererWithContext
from .markdown_db.index import IndexBuilder, build_index

# Enter absolute path to the file for debugging.
# e.g.: "/Users/john/mkdocs-dataview-plugin/docs/examples/library/index.md"
__debug_log_file__ = None


class DataViewPluginConfig(base.Config):
    """Config file for the mkdocs plugin."""


class DataViewPlugin(BasePlugin[DataViewPluginConfig], IndexBuilder):
    """Data View plugin main class."""
    def __init__(self):
        self.sources = {}
        self.tags = defaultdict(list)
        self.renderer = RendererWithContext(self.sources)
        self._log_toggle = False

    def _log(self, *args, **kwargs) -> None:
        if self._log_toggle:
            print(*args, **kwargs)

    def add_tag(self, tag: str, metadata: dict) -> None:
        self.tags[tag].append(metadata)

    def add_file(self, file_path: str, metadata: dict) -> None:
        self.sources[file_path] = metadata

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        genderated_files_list = []
        for f in files:
            path_without_extension, extension = os.path.splitext(f.src_uri)
            if extension in ['.mdtmpl']:
                genderated_files_list.append(path_without_extension)

        for f in genderated_files_list:
            rf = files.src_uris.get(f + '.md')
            if rf:
                files.remove(rf)
            tplf = files.src_uris[f + '.mdtmpl']

            # maybe this logic should be more complicated (check for .md modificaiton with
            # existing .mdtmpl)
            # copy .mdtmpl to .md only if it's need. Otherwise mkdocs will enter in infinite loop
            # in serve mode
            abs_target_path = tplf.abs_src_path[:-4]
            if os.path.exists(abs_target_path):
                if os.path.getmtime(abs_target_path) < os.path.getmtime(tplf.abs_src_path):
                    shutil.copyfile(tplf.abs_src_path, tplf.abs_src_path[:-4])

            files.append(File(
                    tplf.src_path[:-4],
                    config['docs_dir'],
                    config['site_dir'],
                    config['use_directory_urls'],
                ))

        for f in files:
            _, extension = os.path.splitext(f.src_uri)
            if extension in ['.md']:
                self._on_file(os.path.join(config.docs_dir, f.src_uri), f.dest_uri)

        return files

    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        """
        Find all dataview fences and replace them with the rendered markdown table
        """

        line_stream = io.StringIO(markdown)
        output = io.StringIO()

        if page.file.abs_src_path == __debug_log_file__:
            self.renderer.toggle_log(True)

        this_metadata = self.sources[os.path.join(config.docs_dir, page.file.src_uri)]

        self.renderer.render_str(line_stream, output, this_metadata, page.url)

        result = output.getvalue()
        output.close()
        self.renderer.toggle_log(False)
        return result

    def load_file(self, path: str):
        """
        Loads a file and processes it with the appropriate processor.
        """
        with open(path, 'r', encoding="utf-8-sig") as file:
            return frontmatter.load(file)

    def _on_file(self, file_path: str, target_url: str):
        """common method to scan file to build index"""

        if os.path.basename(file_path) == __debug_log_file__:
            self._log_toggle = True

        self._log("*"*80)
        self._log("load_file", file_path)

        data = self.load_file(file_path)

        self._log(data.metadata)
        self._log("*"*80)
        build_index(data, file_path, target_url, self)
        self._log_toggle = False
