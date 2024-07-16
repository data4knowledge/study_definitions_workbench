from model.raw_docx.raw_list import RawList
from model.raw_docx.raw_table import RawTable
from model.raw_docx.raw_paragraph import RawParagraph
from d4kms_generic import application_logger

class RawTableCell():
  
  def __init__(self):
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
    lines = []
    lines.append("<td>")
    for item in self.items:
      lines.append(item.to_html())
    lines.append("</td>")
    return ("\n").join(lines)

