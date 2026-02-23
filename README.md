# mkdocs-dataview-plugin


[![Python package](https://github.com/kepkin/mkdocs-dataview-plugin/actions/workflows/python-package.yml/badge.svg?branch=main)](https://github.com/kepkin/mkdocs-dataview-plugin/actions/workflows/python-package.yml)

Plugin for mkdocs that allows to build markdown tables on metadata

## Overview
**mkdocs-dataview-plugin** is a plugin that makes it easier to build markdown tables on data based on other files metadata during the build step. Typical usecase are: registries, summary pages, section for replated pages based on similar tag.

````
---
title: How to do a heapsort
group_tag: group-sorting-algorithms
tags:
 - group-sorting-algorithms
---

Related algorithms:

```dataview
file.link
WHERE this.file.metadata.group_tag in tags and this.file.title != title
```

````

## Installation

There are two usage options:
 - as mkdocs plugin
 - as a separate tool for gerenating .md files from templates

### Mkdocs plugin

Just add `dataview` to plugin list in `mkdocs.yml`, no other configuration is required.

```
plugins:
  - dataview
```

### As a separate tool

In case you can't use plugin option, write markdowns files with `dataview`

## Development

Prepare environment

````
python -m venv .venv
source .venv/bin/activate

pip install .
```

Do some changes in the code and run tests:

```bash
pytest
```

You should also check that examples folder is working just by running:

```bash
mkdocs serve
```