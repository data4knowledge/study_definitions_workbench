from model.word_docx.table_cell import TableCell
from d4kms_generic import application_logger

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

