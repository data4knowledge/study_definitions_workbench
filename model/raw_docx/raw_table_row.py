from model.raw_docx.raw_table_cell import RawTableCell
from d4kms_generic import application_logger

class RawTableRow():
  
  def __init__(self):
    self.cells = []
  
  def add(self, cell: RawTableCell):
    self.cells.append(cell) 
  
  def to_html(self):
    lines = []
    lines.append("<tr>")
    for item in self.cells:
      lines.append(item.to_html())
    lines.append("</tr>")
    return ("\n").join(lines)

