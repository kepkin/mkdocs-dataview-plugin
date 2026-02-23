# User Guide

This plugin allows you to query your Markdown files and render the results seamlessly within your documentation as dynamically generated lists or tables or inline values.

## What data can be queried

If markdown has a frontmatter, you can use it for filtering and displaying data.

Here is a simple .md file containing information about a book:

```markdown
---
author: John Doe
tags: ["book"]
genre: fantasy
---

# My Book

This is a book by John Doe.
```

So now you can query the data in the following way:

    ```dataview
    TABLE file.link as "Title", metadata.author as "Author"
    FROM #book
    WHERE metadata.genre = "fantasy"
    ```

You can check example library for more advanced queries in the [library](examples/library.md) page.

## Forming a Query

Queries are written inside Markdown code blocks annotated with `dataview`. The query syntax is SQL-like with some support for functions.

A standard query looks like this:


    ```dataview
    TABLE file.link as "Title", metadata.author as "Author"
    FROM "examples/library"
    WHERE metadata.genre == "Fantasy"
    ```


The general structure contains up to three main clauses:

1. **View Type**: `TABLE` or `LIST`. Indicates how you want to display the results.
2. **Columns**: Next to it, you specify the columns or fields to select.
3. **FROM Clause**: Usually a path like `"folder/path"` or a tag like `#some_tag` indicating where to search for files.
4. **WHERE Clause (optional)**: Filter expressions to only show files matching certain criteria.

## Columns

You can rename columns in the query output by using the `as` keyword. This is extra handy in case you do some calculations. Aliases must be enclosed in double quotes.


    ```dataview
    TABLE metadata.rating_age > 19 as "For Adults"
    ```
    
This will render columnt with True/Fales values. If file doesn't have specific field, it will be treated as empty string.

## From Clause

Since there are no tables as in a traditional database, we call them sources. Right now joins are not supported, and it is not possible to query data from multiple sources. You must specify either a path or a tag.

Path source will include all files under the path. For instance if you have the following folder structure:

``` 
docs
├── folder1
├── library
│   ├── index.md
│   ├── book_1.md
│   ├── book_2.md
│   └── sub_library
│       ├── book_10.md
│       ├── book_11.md
│       ├── book_12.md
```

and the query will have `FROM "library"` then it will include all files under the `library` folder and under `sub_library` folder.

Tag source always start with `#` while tags in the frontmatter should not have `#`.

## Where Clause

Supports the following operators:

### Comparison Operators

- `==` Check if two values are equal.
- `!=` Check if two values are not equal.
- `<` Less than.
- `>` Greater than.
- `<=` Less than or equal to.
- `>=` Greater than or equal to.
- `IN` Checks if an item exists within a list (e.g., `metadata.status IN ["Draft", "Review"]`).
- `CONTAINS` Checks whether a string contains another substring or if an array contains an item (e.g., `metadata.tags CONTAINS "Science"`).

### Logical Operators

Combine multiple conditions:

- `AND`: True if both conditions are true.
- `OR`: True if at least one condition is true.
- `NOT`: Inverts the logic of an expression.

### Mathematical Operators

Standard arithmetic is also available:

- `+` Addition
- `-` Subtraction
- `*` Multiplication
- `/` Division


## Special `this` Attribute

Inside queries, the `this` attribute refers to the metadata of the **current** file containing the query. It is extremely useful in the `WHERE` clause when you want to filter other files dynamically relative to the current working document.

For example, to find other files sharing the same author as the current page:


    ```dataview
    TABLE file.link as "Title"
    FROM "examples/library"
    WHERE metadata.author == this.author
    ```


## Inline Queries in the Same File

In addition to full code blocks, you can perform quick metadata evaluations inline throughout the text.

Inline queries are written using backticks starting with `= `. For example:

An inline query looking for the current page author looks like this: `= this.author`.

When MkDocs builds the site, `` `= this.author` `` will be evaluated and replaced by the actual author value from the file's frontmatter.

## Operators Reference (WHERE Clause)

The plugin supports a robust set of logical, mathematical, and comparative operators allowing you to create complex queries in your `WHERE` clauses.


