"""
This module allows to render 'dataview' fences based on collected data in metadata in .md files.
"""
from abc import ABC, abstractmethod
from collections import defaultdict
import io
import os
import shutil

import dictquery as dq
import frontmatter

from jinja2.sandbox import SandboxedEnvironment
from mkdocs.config import base
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files, File
from mkdocs.structure.pages import Page

from . import utils

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

        this_metadata = self.sources[os.path.join(config.docs_dir, page.file.src_uri)]
        self.render_str(line_stream, output, this_metadata, page.url)

        result = output.getvalue()
        output.close()
        return result

    def load_file(self, path: str):
        """
        Loads a file and processes it with the appropriate processor.
        """
        with open(path, 'r', encoding="utf-8-sig") as file:
            return frontmatter.load(file)

    def _on_file(self, file_path: str, target_url: str):
        """common method to scan file to build index"""
        data = self.load_file(file_path)
        build_index(data, file_path, target_url, self)

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

                out.write(line)

            else:
                if line.rstrip() == "```":
                    self.render_query(query, this_metadata, out, path)
                    in_data_view = False
                    query = ""
                    continue

                query += line

    def render_file(self, path, out):
        """renders file"""
        obj = self.load_file(path)
        self.render_str(io.StringIO(obj.content), out, obj.metadata, path)

    def render_all_templates(self, path: str):
        """renders all files in cli mode"""
        for full_path_file in utils.enumerate_files_by_ext(path, ['.mdtmpl']):
            new_file_path, _ = os.path.splitext(full_path_file)
            new_file_path += ".md"

            with open(new_file_path, 'w', encoding="utf-8-sig") as file_out:
                self.render_file(full_path_file, file_out)

    def render_query(self, query, this_metadata, out, out_path=''):
        """replaces context variable in where clause and then renders markdown table"""
        select_list_str, where_query = query.split("WHERE",2)
        select_list = [i.strip() for i in select_list_str.split(',')]

        rendered_where_query = self.render_where_clause(where_query, this_metadata)
        return self.render_table(select_list, rendered_where_query, out, out_path)


    def render_where_clause(self, where_query, this_metadata): # pylint: disable=too-many-branches
        """replaces context variable in where clause"""
        result = []

        for t in split_token(where_query):
            t = t.strip()
            if t.startswith('this.'):
                lookup_value = this_metadata

                for k in t[len('this.'):].split('.'):
                    lookup_value = lookup_value.get(k)
                    if lookup_value is None:
                        break

                result.append(repr(lookup_value))
            elif t.startswith('`this.'):
                lookup_value = this_metadata

                for k in t[len('`this.'):-1].split('.'):
                    lookup_value = lookup_value.get(k)
                    if lookup_value is None:
                        break

                result.append(repr(lookup_value))

            # make split_token return type of token and process only variables.
            elif t in ['+', '-', '*', '/', '!=', '==',
                       '[', ']', ',', '(', ')',
                       'and', 'or', 'AND', 'OR', 'not', 'NOT',
                       'in', 'IN', 'CONTAINS', 'contains',
                       'null', 'NULL']:
                result.append(t)
            elif t.startswith('"'):
                result.append(t)
            elif t.startswith("'"):
                result.append(t)
            elif t.startswith('`metadata.'):
                result.append(t)
            elif t.startswith('`file.'):
                result.append(t)
            elif t == 'metadata':
                result.append(t)
            elif t == '`metadata`':
                result.append(t)
            else:
                if t[0] == '`':
                    t = t[1:-1]
                result.append('`metadata.' + t + '`')

        return ' '.join(result)

    def render_table(self, select_list, where_query, out, out_path):
        """renders markdown table"""
        env = SandboxedEnvironment()

        render_table_header(select_list, out)

        tpl = "|"
        for v in select_list:
            tpl += " {{ dataview['" + "']['".join(v.split('.')) + "'] }} |"

        for _, v in self.sources.items():
            v['file']['link'] = f"[{v['metadata'].get('title', os.path.basename(v['file']['path']))}]({os.path.relpath(v['file']['path'], os.path.dirname(out_path))})" # pylint: disable=line-too-long
            try:
                if not dq.match(v, where_query):
                    continue
                out.write(env.from_string(tpl).render(dataview=v))
                out.write("\n")
            except Exception as exc:
                # raises already post processed where_query
                raise Exception(where_query, tpl, v) from exc # pylint: disable=broad-exception-raised



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


def split_token(where_query):
    """generator for where clause tokens"""
    token = ""
    constant_phase = ''
    for i in where_query:
        if i in ["'", '"', '`'] and constant_phase == '':
            constant_phase = i
            if token:
                yield token
                token = ""
            token += i
            continue

        if constant_phase != '':
            token += i
            if i == constant_phase:
                constant_phase = ''
                yield token
                token = ""
            continue

        if i in [',', '(', ')', '+', '-', '*', '/', '[', ']', '!=', '==']:
            if token:
                yield token
                token = ""
            yield i
            continue

        if i in [' ', '\t', '\n']:
            if token:
                yield token

            token = ""
            continue

        token += i

    if token:
        yield token
