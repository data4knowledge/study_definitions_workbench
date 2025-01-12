from d4kms_generic import application_logger
from app.model.raw_docx.raw_list_item import RawListItem


class RawList:
    def __init__(self, level=0):
        self.items = []
        self.level = level

    def add(self, item: RawListItem) -> None:
        if item.level == self.level:
            self.items.append(item)
        elif item.level > self.level:
            list = self.items[-1] if self.items else None
            if not isinstance(list, RawList):
                list = RawList(item.level)
                self.items.append(list)
            list.add(item)
            if item.level > self.level + 1:
                application_logger.warning(
                    f"Adding list item '{item}' to item but level jump greater than 1"
                )
        else:
            application_logger.error(
                f"Failed to add list item '{item}' to list '{self}', levels are in error"
            )

    def to_html(self):
        lines = []
        lines.append("<ul>")
        for item in self.items:
            lines.append(f"<li>{item.to_html()}</li>")
        lines.append("</ul>")
        return ("\n").join(lines)

    def __str__(self):
        return f"[level='{self.level}', item_count='{len(self.items)}']"
