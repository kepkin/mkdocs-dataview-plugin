---
title: Library Catalog
---

# Library Catalog


### Get books that fullfills condition

Table of all books that has Edgar award with folliwing query.

```
TABLE file.link as "Title",
metadata.author as "Author",
metadata.publishing_date as "Date",
FROM "examples/library"
WHERE metadata.awards contains "Edgar Award"
```

```dataview
TABLE file.link as "Title",
metadata.author as "Author",
metadata.genre as "Genre",
metadata.publishing_date as "Date"
FROM "examples/library"
WHERE metadata.awards contains "Edgar Award"
```

### Example for making index of all items

Table of all books. But you need to write condtion to exclude this file (e.g. index.md).

```
TABLE file.link as "Title",
metadata.author as "Author",
metadata.genre as "Genre",
metadata.publishing_date as "Date"
FROM "examples/library"
WHERE metadata.author != ""
```

```dataview
TABLE file.link as "Title",
metadata.author as "Author",
metadata.genre as "Genre",
metadata.publishing_date as "Date"
FROM "examples/library"
WHERE metadata.author != ""
```