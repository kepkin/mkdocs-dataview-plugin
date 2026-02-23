import io
import os
import frontmatter

from .md_renderer import RendererWithContext
from .index import build_index, SimpleMemoryIndex
from .. import utils


__debug_log_file__ = None


class FilePlugin():
    def __init__(self):
        self.index = SimpleMemoryIndex()
        self.sources = {}
        self.renderer = RendererWithContext(self.sources)
        self.log_toggle = False

    def toggle_log(self, v: bool) -> None:
        """turns on/off debug logging"""
        self.log_toggle = v

    def _log(self, *args, **kwargs) -> None:
        """use it for debugging"""
        if self.log_toggle:
            print(*args, **kwargs)

    def render_file(self, path, out):
        """renders file"""
        obj = self.load_file(path)
        # cause obj.metadata doesn't have metadata, we had to render it first here
        out.write("---\n")
        out.write("generated_ignore: true\n")
        out.write(frontmatter.YAMLHandler().export(obj.metadata))
        out.write("\n---\n")
        self.renderer.render_str(io.StringIO(obj.content), out, self.sources[path], path)

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

    def load_file(self, path: str):
        """
        Loads a file and processes it with the appropriate processor.
        """
        with open(path, 'r', encoding="utf-8-sig") as file:
            return frontmatter.load(file)

    def _on_file(self, file_path: str, target_url: str):
        """common method to scan file to build index"""

        data = self.load_file(file_path)

        build_index(data, file_path, target_url, self.index)
        self.log_toggle = False

    def collect_data(self, root_path: str):
        """searches for all .md, .mdtmpl files (used in cli mode)"""
        for file_path in utils.enumerate_files_by_ext(root_path, ['.md', '.mdtmpl']):
            target_url = file_path
            path_without_extension, extension = os.path.splitext(file_path)
            if extension == '.mdtmpl':
                target_url = path_without_extension + '.md'
            self._on_file(file_path, target_url)
