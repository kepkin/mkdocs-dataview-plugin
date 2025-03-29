"""
This module allows to render 'dataview' fences based on collected data in metadata in .md files.
"""
from collections import defaultdict
import io
import os
import shutil

import dictquery as dq
import frontmatter

from jinja2.sandbox import SandboxedEnvironment
from mkdocs.config import base
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import Files, File
from mkdocs.structure.pages import Page

from . import utils

class DataViewPluginConfig(base.Config):
    """Config file for the mkdocs plugin."""

class DataViewPlugin(BasePlugin[DataViewPluginConfig]):
    """Data View plugin main class."""
    def __init__(self):
        self.sources = {}
        self.tags = defaultdict(list)

    def on_files(self, files: Files, config, **kwargs):
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

    def on_page_markdown(self, markdown, page: Page, config, **kwargs):
        """
        Find all dataview fences and replace them with the rendered markdown table
        """

        line_stream = io.StringIO(markdown)
        output = io.StringIO()
        self.render_str(line_stream, output, page.meta, page.url)

        result = output.getvalue()
        output.close()
        return result


    def load_file(self, path: str):
        """
        Loads a file and processes it with the appropriate processor.
        """
        with open(path, 'r', encoding="utf-8-sig") as file:
            return frontmatter.load(file)

    def _on_file(self, path: str, target_url: str):
        obj = self.load_file(path)
        if obj.metadata.get("generated_ignore"):
            return

        if obj.metadata.get('file') is not None:
            raise Exception("unexpected `file` parameter in frontmatter ", path)

        obj.metadata['file'] = {
            'path': target_url,
            'name': os.path.basename(path)
        }
        self.sources[path] = obj.metadata

        if 'tags' in obj.metadata:
            for tag in obj.metadata['tags']:
                self.tags[tag].append(obj.metadata)

    def collect_data(self, root_path: str):
        for file_path in utils.enumerate_files_by_ext(root_path, ['.md', '.mdtmpl']):
            target_url = file_path
            path_without_extension, extension = os.path.splitext(file_path)
            if extension == '.mdtmpl':
                target_url = path_without_extension + '.md'
            self._on_file(file_path, target_url)


    def render_str(self, line_stream, out, metadata, path):
        frontmatter_expecting = True

        in_data_view = False
        query = ""
        for l in line_stream:
            if frontmatter_expecting:
                frontmatter_expecting = False
                if l.strip() == "---":
                    out.write(l)
                    out.write("generated_ignore: true\n")
                    continue


            if not in_data_view:
                if l == "```dataview\n":
                    in_data_view = True
                    continue

                out.write(l)

            else:
                if l == "```\n":
                    self.render_query(query, metadata, out, path)
                    in_data_view = False
                    query = ""
                    continue

                query += l

    def render_file(self, path, out):
        obj = self.load_file(path)
        self.render_str(io.StringIO(obj.content), out, obj.metadata, path)

    def render_all_templates(self, path: str):
        for full_path_file in utils.enumerate_files_by_ext(path, ['.mdtmpl']):
            new_file_path, _ = os.path.splitext(full_path_file)
            new_file_path += ".md"

            with open(new_file_path, 'w') as file_out:
                self.render_file(full_path_file, file_out)


    def render_query(self, query, metadata, out, out_path=''):
        select_list_str, where_query = query.split("WHERE",2)
        select_list = [i.strip() for i in select_list_str.split(',')]

        rendered_where_query = self.render_where_clause(where_query, metadata)
        return self.render_table(select_list, rendered_where_query, out, out_path)

    def split_token(self, where_query):
        token = ""
        for i in where_query:
            if i in [',' '(', ')', '+', '-', '*', '/', '[', ']']:
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

    def render_where_clause(self, where_query, metadata):
        result = []

        for t in self.split_token(where_query):
            t = t.strip()
            if t.startswith('this.file.metadata.'):
                t = repr(metadata.get(t[len('this.file.metadata.'):]))
            result.append(t)

        return ' '.join(result)

    def render_table(self, select_list, where_query, out, out_path):
        env = SandboxedEnvironment()

        out.write("|")
        out.write("|".join(select_list))
        out.write("|\n")
        out.write("|")
        out.write("--|"*len(select_list))
        out.write("\n")

        tpl = "|"
        for v in select_list:
            if v.split('.', 1)[0] == "file":
                tpl += f" {{{{ el.{v} }}}} |"
            else:
                tpl += f" {{{{ el['{v}'] }}}} |"

        for _, v in self.sources.items():
            v['file']['link'] = f"[{v.get('title', os.path.basename(v['file']['path']))}]({os.path.relpath(v['file']['path'], os.path.dirname(out_path))})"
            try:
                if not dq.match(v, where_query):
                    continue
            except Exception as exc:
                raise Exception(where_query) from exc
            out.write(env.from_string(tpl).render(el=v))
            out.write("\n")

