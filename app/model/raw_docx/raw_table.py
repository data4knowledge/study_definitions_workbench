# from app.model.raw_docx.raw_paragraph import RawParagraph
# from app.model.raw_docx.raw_list import RawList
# from d4k_ms_base.logger import application_logger
# from app.model.raw_docx.raw_table_row import RawTableRow


class RawTable:
    def __init__(self):
        from app.model.raw_docx.raw_table_row import RawTableRow

        self.rows: list[RawTableRow] = []
        self.klasses = ["ich-m11-table"]

    # @ToDo Would like RawTableRow here but gets a circular import
    def add(self, item):
        self.rows.append(item)

    def row(self, index: int):
        return self.rows[index] if (index) < len(self.rows) else None

    def next(self, index: int) -> tuple[object, int]:
        return (
            (self.rows[index + 1], index + 1)
            if (index + 1) < len(self.rows)
            else (None, -1)
        )

    def find_row(self, text: str) -> tuple[object, int]:
        for index, row in enumerate(self.rows):
            if row.cells[0].is_text():
                if text.upper() in row.cells[0].text().upper():
                    return row, index
        return None, -1

    def to_html(self):
        lines = []
        klass_list = " ".join(self.klasses)
        open_tag = f'<table class="{klass_list}">' if self.klasses else "<table>"
        lines.append(open_tag)
        for item in self.rows:
            lines.append(item.to_html())
        lines.append("</table>")
        return ("\n").join(lines)

    def add_class(self, klass):
        self.klasses.append(klass)

    def replace_class(self, old_klass, new_klass):
        self.klasses.remove(old_klass)
        self.klasses.append(new_klass)
