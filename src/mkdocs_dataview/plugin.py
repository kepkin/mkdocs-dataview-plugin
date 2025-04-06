"""
This module allows to render 'dataview' fences based on collected data in metadata in .md files.
"""
from abc import ABC, abstractmethod
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
from mkdocs_dataview.parser import (
    execute_expression_list,
    execute_where_clause,
    execute_get_select_column_names,
)

from . import utils

__debug_log_file__ = None

class IndexBuilder(ABC):
    """Interface for building an Index"""
    @abstractmethod
    def add_tag(self, tag: str, metadata: dict) -> None: # pylint: disable=missing-function-docstring
        pass

    @abstractmethod
    def add_file(self, file_path: str, metadata: dict) -> None: # pylint: disable=missing-function-docstring
        pass


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

    def on_files(self, files: Files, *, config: MkDocsConfig) -> Files | None:
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
        self, markdown: str, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str:
        """
        Find all dataview fences and replace them with the rendered markdown table
        """

        line_stream = io.StringIO(markdown)
        output = io.StringIO()

        if os.path.basename(page.file.abs_src_path) == __debug_log_file__:
            self.renderer.toggle_log(True)

        this_metadata = self.sources[os.path.join(config.docs_dir, page.file.src_uri)]
        self.render_str(line_stream, output, this_metadata, page.url)

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

    def collect_data(self, root_path: str):
        """searches for all .md, .mdtmpl files (used in cli mode)"""
        for file_path in utils.enumerate_files_by_ext(root_path, ['.md', '.mdtmpl']):
            target_url = file_path
            path_without_extension, extension = os.path.splitext(file_path)
            if extension == '.mdtmpl':
                target_url = path_without_extension + '.md'
            self._on_file(file_path, target_url)

    def render_str(self, line_stream, out, this_metadata, path):
        """renders from line_stream to out"""
        frontmatter_expecting = True

        in_data_view = False
        query = ""
        for line in line_stream:
            if frontmatter_expecting:
                frontmatter_expecting = False
                if line.strip() == "---":
                    out.write(line)
                    out.write("generated_ignore: true\n")
                    continue

            if not in_data_view:
                if line == "```dataview\n":
                    in_data_view = True
                    continue

                self.render_line(line, this_metadata, out)

            else:
                if line.rstrip() == "```":
                    self.renderer.render_query(query, this_metadata, out, path)
                    in_data_view = False
                    query = ""
                    continue

                query += line

    def render_line(self, line, this_metadata, out) -> str:
        """allows to render inplace datavew queries"""
        for line_part in split_inline_query(line):
            if line_part.startswith("`= "):
                identifiers = {}
                identifiers['this'] = this_metadata
                print("---- RENDER")

                result = execute_expression_list(line_part[3:-1], identifiers)
                print(line_part[3:-1])
                print(result)
                out.write(result[0])
                continue
            out.write(line_part)

    def render_file(self, path, out):
        """renders file"""
        obj = self.load_file(path)
        # cause obj.metadata doesn't have metadata, we had to render it first here
        out.write("---\n")
        out.write("generated_ignore: true\n")
        out.write(frontmatter.YAMLHandler().export(obj.metadata))
        out.write("\n---\n")
        self.render_str(io.StringIO(obj.content), out, self.sources[path], path)

    def render_all_templates(self, path: str):
        """renders all files in cli mode"""
        for full_path_file in utils.enumerate_files_by_ext(path, ['.mdtmpl']):
            new_file_path, _ = os.path.splitext(full_path_file)
            new_file_path += ".md"

            if os.path.basename(new_file_path) == __debug_log_file__:
                self.renderer.toggle_log(True)

            with open(new_file_path, 'w', encoding="utf-8-sig") as file_out:
                self.render_file(full_path_file, file_out)

            self.renderer.toggle_log(False)


class RendererWithContext:
    """Class for rendering dataview queries based on context"""

    def __init__(self, sources):
        self.sources = sources
        self.log_toggle = False

    def toggle_log(self, v: bool) -> None:
        """turns on/off debug logging"""
        self.log_toggle = v

    def log(self, *args, **kwargs) -> None:
        """use it for debugging"""
        if self.log_toggle:
            print(*args, **kwargs)

    def render_table(self, select_list, where_query, this_metadata, out, out_path):  # pylint: disable=too-many-positional-arguments,too-many-arguments
        """renders markdown table"""

        render_table_header(execute_get_select_column_names(select_list), out)

        for _, v in self.sources.items():
            identifiers = {}
            identifiers['metadata'] = v['metadata']
            identifiers['this'] = this_metadata
            identifiers['file'] = v['file']
            identifiers['file']['link'] = f"[{v['metadata'].get('title', os.path.basename(v['file']['path']))}]({os.path.relpath(v['file']['path'], os.path.dirname(out_path))})" # pylint: disable=line-too-long
            try:
                match = execute_where_clause(where_query, identifiers)
                self.log("------")
                self.log("   query:", where_query)
                self.log("   match:", match, identifiers)

                if not match:
                    continue

                row_list = execute_expression_list(select_list, v)
                out.write("|")
                out.write("|".join([str(i) for i in row_list]))
                out.write("|\n")
            except Exception as exc:
                # raises already post processed where_query
                raise Exception(where_query, select_list, v) from exc # pylint: disable=broad-exception-raised

    def render_query(self, query, this_metadata, out, out_path=''):
        """replaces context variable in where clause and then renders markdown table"""
        select_list_str, expression = query.split("WHERE",2)
        return self.render_table(
            select_list_str,
            "WHERE " + expression,
            this_metadata,
            out,
            out_path
        )


def render_table_header(select_list, out):
    """renders markdown table header"""
    out.write("|")
    out.write("|".join(select_list))
    out.write("|\n")
    out.write("|")
    out.write("--|"*len(select_list))
    out.write("\n")


def build_index(
        data: frontmatter.Post,
        file_path: str,
        target_url: str,
        builder: IndexBuilder
        ) -> None:
    """
    Updates index from frontmatter.Post object
    """
    if data.metadata.get("generated_ignore"):
        return

    if data.metadata.get('file') is not None:
        raise Exception("unexpected `file` parameter in frontmatter ", file_path) # pylint: disable=broad-exception-raised

    result_dataview_metadata = {
        "metadata": data.metadata,
        "file": {
            'path': target_url,
            'name': os.path.basename(file_path)
        }
    }

    builder.add_file(file_path, result_dataview_metadata)

    if 'tags' in data.metadata:
        for tag in data.metadata['tags']:
            builder.add_tag(tag, result_dataview_metadata)


def split_inline_query(line):
    """splits linke into text and ticks part"""
    i = 0

    while i <= len(line):
        next_l = line.find("`", i)
        if next_l == -1:
            yield line[i:]
            return

        next_r = line.find("`", next_l + 1)
        if next_r == -1:
            yield line[i:]
            return

        yield line[i:next_l]
        yield line[next_l:next_r+1]
        i = next_r+1
