# Architecture

## Overview

`mkdocs-dataview-plugin` is a plugin for [MkDocs](https://www.mkdocs.org/) that allows users to query and display data from their Markdown files using a SQL-like syntax, similar to the Obsidian Dataview plugin.

## Core Components

### 1. Plugin Entry Point (`plugin.py`)
The `DataViewPlugin` class extends `mkdocs.plugins.BasePlugin`. It hooks into the MkDocs build lifecycle:
- `on_files`: Scans for `.mdtmpl` files (templates) and prepares them.
- `on_page_markdown`: The main hook. It finds `dataview` code blocks in the Markdown content and replaces them with rendered tables or lists.
- `_on_file`: Scans files to build an in-memory index of metadata (`self.sources` and `self.tags`).

### 2. The query modeule
The plugin uses [Lark](https://github.com/lark-parser/lark) to parse the query language.
- `LARK_GRAMMAR`: Defines the EBNF grammar for the query language (FROM, WHERE, SELECT clauses).
- TBD: `solvers.py`

