import os
import base64
from logger import application_logger
#from docx import Document as doc
#from docx.document import Document
#from docx.oxml.table import CT_Tbl, CT_TcPr
#from docx.oxml.text.paragraph import CT_P
#from docx.table import _Cell, Table
#from docx.text.paragraph import Paragraph
#from lxml import etree

class RawImage():

  FILE_TYPE_MAP = {'.png': 'png', '.jpg': 'jpg', '.jpeg': 'jpg'}

  def __init__(self, filepath: str):
    self.filepath = filepath

  def to_html(self):
    try:
      file_root, file_extension = os.path.splitext(self.filepath)
      with open(self.filepath, "rb") as image_file:
        data = base64.b64encode(image_file.read())
      file_type = self.FILE_TYPE_MAP[file_extension]
      decoded = data.decode("ascii")
      return f"<img alt=\"alt text\" src=\"data:image/{file_type};base64,{decoded}\"/>"
    except Exception as e:
      application_logger.exception("Exception converting image", e)
      return ""

class RawParagraph():

  def __init__(self, text: str):
    self.text = text.strip()

  def to_html(self):
    return f"<p>{self.text}</p>"

class RawListItem():

  def __init__(self, text: str, level: int):
    self.text = text
    self.level = level

  def to_html(self):
    return f"{self.text}"

  def __str__(self):
    return f"[text='{self.text}', level='{self.level}']"
  
class RawList():

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
        application_logger.warning(f"Adding list item '{item}' to item but level jump greater than 1")
    else:
      application_logger.error(f"Failed to add list item '{item}' to list '{self}', levels are in error")

  def to_html(self):
    lines = []
    lines.append("<ul>")
    for item in self.items:
      lines.append(f"<li>{item.to_html()}</li>")
    lines.append("</ul>")
    return ("\n").join(lines)

  def __str__(self):
    return f"[level='{self.level}', item_count='{len(self.items)}']"

class RawTable():

  def __init__(self):
    self.rows = []
  
  def add(self, item: 'RawTableRow'):
    self.rows.append(item) 

  def to_html(self):
    lines = []
    lines.append("<table>")
    for item in self.rows:
      lines.append(item.to_html())
    lines.append("</table>")
    return ("\n").join(lines)

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

class RawSection():

  def __init__(self, title: str | None, number: str | None, level: int):
    self.title = title.strip() if title else title
    self.number = number.strip() if number else number
    self.level = level
    self.items = []

  def add(self, item: RawParagraph | RawList | RawTable | RawImage) -> None:
    self.items.append(item)

  def is_in_list(self) -> bool:
    if self.items:
      if isinstance(self.items[-1], RawList):
        return True
    return False
  
  def current_list(self) -> RawList:
    return self.items[-1] if isinstance(self.items[-1], RawList) else None

  def to_dict(self):
    return { 'sectionNumber': self.number, 'sectionTitle': self.title, 'name': '', 'text': self.to_html()} 

  def to_html(self):
    text = [self._format_heading()]
    for item in self.items:
      result = item.to_html()
      text.append(result)
    return ('\n').join(text)

  def tables(self):
    return [x for x in self.items if isinstance(x, RawTable)]

  def _format_heading(self):
    if self.number and self.title:
      return f'<h{self.level}>{self.number} {self.title}</h{self.level}>'
    elif self.number:
      return f'<h{self.level}>{self.number}</h{self.level}>'
    elif self.title:
      return f'<h{self.level}>{self.title}</h{self.level}>'
    else:
      return ''
        
class RawDocument():
  
  def __init__(self):
    self.sections = []
    self._levels = [0,0,0,0,0,0]
    self._section_number_mapping = {} 
    self._section_title_mapping = {} 
    section = RawSection(None, None, 1)
    self.add(section, False) # No section number increment

  def add(self, section: RawSection, increment=True):
    if increment:
      self._inc_section_number(section.level)
      section.number = self._get_section_number(section.level)
    self._section_number_mapping[section.number] = section
    self._section_title_mapping[section.title] = section
    self.sections.append(section)

  def current_section(self) -> RawSection:
    return self.sections[-1]

  def section_by_ordinal(self, ordinal: int) -> RawSection:
    if 1 >= ordinal <= len(self.sections):
      return self.sections[ordinal - 1]
    else:
      application_logger.error(f"Could not find section in ordinal position '{ordinal}'")
      return None

  def section_by_number(self, section_number: str) -> RawSection:
    if section_number in self._section_number_mapping:
      return self._section_number_mapping[section_number] 
    else:
      application_logger.error(f"Could not find section with number '{section_number}'")
      return None

  def section_by_title(self, section_title: str) -> RawSection:
    if section_title in self._section_title_mapping:
      return self._section_title_mapping[section_title] 
    else:
      application_logger.error(f"Could not find section with title '{section_title}'")
      return None

  def _inc_section_number(self, level: int) -> None:
    try: 
      self._levels[level] += 1
      for index in range(level+1, len(self._levels)):
        self._levels[index] = 0
    except Exception as e:
      application_logger.exception(f"Failed to increment section number from levels '{self._levels}'", e)

  def _get_section_number(self, level: int) -> str:
    try:
      return '.'.join(str(x) for x in self._levels[1:level+1])
    except Exception as e:
      application_logger.exception(f"Failed get section number from levels '{self._levels}'", e)
