from model.docx.paragraph import Paragraph
from model.docx.list import List
from model.docx.table import Table
from d4kms_generic import application_logger

class Table():

  def __init__(self):
    self.rows = []
  
  def add(self, item: 'TableRow'):
    self.rows.append(item) 

  def to_html(self):
    lines = []
    lines.append("<table>")
    for item in self.rows:
      lines.append(item.to_html())
    lines.append("</table>")
    return ("\n").join(lines)

class TableCell():
  
  def __init__(self):
    self.items = []
  
  def add(self, item: Paragraph | List | Table) -> None:
    self.items.append(item) 

  def is_text(self) -> bool:
    for item in self.items:
      if not isinstance(item, Paragraph):
        return False
    return True

  def text(self) -> str:
    return ("\n").join([x.text for x in self.items])

  def is_in_list(self) -> bool:
    if self.items:
      if isinstance(self.items[-1], List):
        return True
    return False

  def current_list(self) -> List:
    return self.items[-1] if isinstance(self.items[-1], List) else None

  def to_html(self):
    lines = []
    lines.append("<td>")
    for item in self.items:
      lines.append(item.to_html())
    lines.append("</td>")
    return ("\n").join(lines)

class TableRow():
  
  def __init__(self):
    self.cells = []
  
  def add(self, cell: TableCell):
    self.cells.append(cell) 
  
  def to_html(self):
    lines = []
    lines.append("<tr>")
    for item in self.cells:
      lines.append(item.to_html())
    lines.append("</tr>")
    return ("\n").join(lines)

