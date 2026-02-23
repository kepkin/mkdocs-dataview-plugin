import os
from mkdocs_dataview.query.solvers import ExpressionSolverService
from mkdocs_dataview.query.solvers import QueryService


class RenderError(Exception):
    pass


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

    # pylint: disable=too-many-positional-arguments,too-many-arguments
    def _render_table_source(self, qs, this_metadata, out, out_path, v):
        sources = qs.get_sources()

        identifiers = {}
        identifiers['metadata'] = v['metadata']
        identifiers['this'] = this_metadata
        identifiers['file'] = v['file']
        file_title = v['metadata'].get('title', os.path.basename(v['file']['path']))
        file_link = os.path.relpath(v['file']['path'], os.path.dirname(out_path))
        identifiers['file']['link'] = f"[{file_title}]({file_link})"
        try:
            include_file = True
            for source in sources:
                if source["type"] == "tag":
                    include_file = include_file and source["value"] in v['metadata'].get("tags", [])
                elif source["type"] == "path":
                    include_file = include_file and v['file']['path'].startswith(source["value"])

                if not include_file:
                    break

            if not include_file:
                return

            match = qs.where(identifiers)
            self.log("------ check file: ", identifiers['file']['link'])
            self.log("   query:", qs.get_where_expression())
            self.log("   match:", match, identifiers)

            if not match:
                return

            row_list = qs.render_columns(v)
            out.write("|")
            out.write("|".join([str(i) for i in row_list]))
            out.write("|\n")
        except Exception as exc:
            raise RenderError() from exc

    def render_table(self, qs, this_metadata, out, out_path):
        """renders markdown table"""

        render_table_header(qs.columns(), out)

        for _, v in self.sources.items():
            self._render_table_source(qs, this_metadata, out, out_path, v)

    def render_list(self, qs, this_metadata, out, out_path):
        """renders markdown list"""
        for _, v in self.sources.items():
            identifiers = {}
            identifiers['metadata'] = v['metadata']
            identifiers['this'] = this_metadata
            identifiers['file'] = v['file']
            file_title = v['metadata'].get('title', os.path.basename(v['file']['path']))
            file_link = os.path.relpath(v['file']['path'], os.path.dirname(out_path))
            identifiers['file']['link'] = f"[{file_title}]({file_link})"

            try:
                # Check FROM clause first
                # if not execute_from_clause(where_query, v):
                #     continue

                match = qs.where(identifiers)
                self.log("------ check file: ", identifiers['file']['link'])
                self.log("   query:", qs.get_where_expression())
                self.log("   match:", match, identifiers)

                if not match:
                    continue

                row_list = qs.render_columns(v)
                if len(row_list) == 0:
                    out.write(f"- {identifiers['file']['link']}\n")
                else:
                    row_value = ', '.join(row_list)
                    out.write(f"- {row_value}\n")

            except Exception as exc:
                raise RenderError() from exc

    def render_query(self, query, this_metadata, out, out_path=''):
        """replaces context variable in where clause and then renders markdown table"""

        try:
            qs = QueryService(query)
        except:
            # @TODO: learn how to raise exception
            print()
            raise

        if qs.get_render_type() == "LIST":
            self.render_table(
                qs,
                this_metadata,
                out,
                out_path
            )
        elif qs.get_render_type() == "LIST":
            self.render_list(
                qs,
                this_metadata,
                out,
                out_path
            )

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
                    self.render_query(query, this_metadata, out, path)
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
                result = ExpressionSolverService(line_part[3:-1]).solve(identifiers)
                out.write(str(result))
                continue
            out.write(line_part)


def render_table_header(select_list, out):
    """renders markdown table header"""
    out.write("|")
    out.write("|".join(select_list))
    out.write("|\n")
    out.write("|")
    out.write("--|"*len(select_list))
    out.write("\n")


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
