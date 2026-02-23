from abc import ABC, abstractmethod
from collections import defaultdict
import os

import frontmatter


class IndexBuilder(ABC):
    """Interface for building an Index"""
    @abstractmethod
    def add_tag(self, tag: str, metadata: dict) -> None:  # pylint: disable=missing-function-docstring
        pass

    @abstractmethod
    def add_file(self, file_path: str, metadata: dict) -> None:  # pylint: disable=missing-function-docstring
        pass


# Builds metadata and links based on paths and frontmatter _PositiveInteger
#
# Does some checks:
#  - ignores file from index if it has attribute `generated_ignore`
#  - does checks that frontmatter doesn't override any "system" attributes like `file`, `ctime`
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
        raise Exception("unexpected `file` parameter in frontmatter ", file_path)  # pylint: disable=broad-exception-raised

    # add a resolver for easy of testing
    # file_stats = os.stat(file_path)
    result_dataview_metadata = {
        "metadata": data.metadata,
        "file": {
            'path': target_url,
            'name': os.path.basename(file_path),
            # add a resolver for easy of testing
            # 'ctime': file_stats.st_ctime,
            # 'mtime': file_stats.st_mtime,
            # 'size': file_stats.st_size,
        }
    }

    builder.add_file(file_path, result_dataview_metadata)

    if 'tags' in data.metadata:
        for tag in data.metadata['tags']:
            builder.add_tag(tag, result_dataview_metadata)


class SimpleMemoryIndex(IndexBuilder):
    def __init__(self):
        self.sources = {}
        self.tags = defaultdict(list)

    def add_tag(self, tag: str, metadata: dict) -> None:
        self.tags[tag].append(metadata)

    def add_file(self, file_path: str, metadata: dict) -> None:
        self.sources[file_path] = metadata
