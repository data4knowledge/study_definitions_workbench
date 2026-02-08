import re
import difflib
from d4k_ms_base.logger import application_logger


class LineRange:
    def __init__(self, line: str, count: str):
        self.line = self._to_int(line)
        self.current = self.line - 1
        self.count = self._to_int(count)

    def next(self):
        self.current += 1

    def _to_int(self, text: str) -> int:
        try:
            return int(text)
        except Exception:
            return 1


class HunkLine:
    TYPE_TO_STYLE = {
        "deleted": "danger",
        "inserted": "success",
        "nochange": "",
        "error": "",
    }

    def __init__(
        self, line: str, old_line_number: int, new_line_number: int, type: str
    ):
        self.line = line[1:]
        self.old_line_number = old_line_number
        self.new_line_number = new_line_number
        self.type = type
        self.style = self.TYPE_TO_STYLE[type]

    def to_html(self) -> str:
        return f"""
    <tr class="m-0 p-0 table-{self.style}">
      <td class="col-auto m-0 p-0 text-center">{self.old_line_number if self.old_line_number else ""}</td>
      <td class="col-auto m-0 p-0 text-center">{self.new_line_number if self.new_line_number else ""}</td>
      <td class="col-auto m-0 p-0">{self.line}</td>
    </tr>
    """


class Hunk:
    def __init__(self, header: str):
        self.header = header
        self.old = None
        self.new = None
        self.lines = []
        matches = re.findall(r"^@@ -(\d+),(\d*) \+(\d+),(\d*) @@.*$", header)
        if matches:
            self.old = LineRange(matches[0][0], matches[0][1])
            self.new = LineRange(matches[0][2], matches[0][3])
        else:
            application_logger.error(f"Failed to decode hunk header '{header}'")

    def add(self, line: str) -> None:
        type = self._set_type(line)
        hl = HunkLine(line, self.old.current, self.new.current, type)
        self.lines.append(hl)

    def _set_type(self, line: str):
        if line.startswith("-"):
            type = "deleted"
            self.old.next()
        elif line.startswith("+"):
            type = "inserted"
            self.new.next()
        elif line.startswith(" "):
            type = "nochange"
            self.old.next()
            self.new.next()
        else:
            type = "error"
        return type


class UnifiedDiff:
    def __init__(self, old_data: list, new_data: list):
        # print(f"UD: Processing...")
        self._hunks = []
        hunk = None
        application_logger.debug("Unified diff processing ...")
        for text in difflib.unified_diff(old_data, new_data):
            application_logger.debug(f"Unified diff text '{text}'")
            # print(f"UD: {text}")
            if text.startswith("---") or text.startswith("+++"):
                pass
            elif text.startswith("@@"):
                application_logger.debug(f"Hunk detected '{text}'")
                hunk = Hunk(text)
                self._hunks.append(hunk)
            else:
                application_logger.debug(f"In Hunk '{text}'")
                if hunk:
                    hunk.add(text)
                else:  # pragma: no cover
                    application_logger.error("Detected diff line with no hunk")

    def to_html(self):
        lines = []
        lines.append('<table class="table responsive w-auto">')
        for index, hunk in enumerate(self._hunks):
            header = f"""<tr class="m-0 p-0">
        <td class="col-auto text-center table-primary m-0 p-0" colspan="2">...</td>
        <td class="col-auto m-0 p-0">{hunk.header}</td>
      </tr>"""
            lines.append(header)
            for item in hunk.lines:
                lines.append(item.to_html())
        lines.append("</table>")
        return ("\n").join(lines)
