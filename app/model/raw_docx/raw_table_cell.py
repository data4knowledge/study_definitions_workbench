# from d4k_ms_base.logger import application_logger
from app.model.raw_docx.raw_paragraph import RawParagraph
from app.model.raw_docx.raw_list import RawList
from app.model.raw_docx.raw_table import RawTable


class RawTableCell:
    def __init__(self, h_span: int = 1, v_span: int = 1, first: bool = True):
        self.h_span = h_span
        self.v_span = v_span
        self.h_merged = h_span > 1
        self.v_merged = v_span > 1
        self.merged = self.h_merged or self.v_merged
        self.first = first
        self.items = []

    def add(self, item: RawParagraph | RawList | RawTable) -> None:
        self.items.append(item)

    def is_text(self) -> bool:
        for item in self.items:
            if not isinstance(item, RawParagraph):
                return False
        return True

    def text(self) -> str:
        return ("\n").join([x.text for x in self.items])

    def is_in_list(self) -> bool:
        if self.items:
            if isinstance(self.items[-1], RawList):
                return True
        return False

    def current_list(self) -> RawList:
        return self.items[-1] if isinstance(self.items[-1], RawList) else None

    def to_html(self):
        if not self.first:
            return ""
        lines = []
        colspan = f' colspan="{self.h_span}"' if self.h_merged else ""
        lines.append(f"<td {colspan}>")
        for item in self.items:
            lines.append(item.to_html())
        lines.append("</td>")
        return ("\n").join(lines)
