from app.model.raw_docx.raw_paragraph import RawParagraph
from app.model.raw_docx.raw_list import RawList
from app.model.raw_docx.raw_table import RawTable
from app.model.raw_docx.raw_image import RawImage
from d4kms_generic import application_logger

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
    #text = [self._format_heading()]
    text = []
    for item in self.items:
      result = item.to_html()
      text.append(result)
    return ('\n').join(text)

  def paragraphs(self) -> list[RawParagraph]:
    return [x for x in self.items if isinstance(x, RawParagraph)]

  def tables(self) -> list[RawTable]:
    return [x for x in self.items if isinstance(x, RawTable)]

  def lists(self) -> list[RawList]:
    return [x for x in self.items if isinstance(x, RawList)]

  def find(self, text) -> list[RawParagraph]:
    return [x for x in self.items if isinstance(x, RawParagraph) and x.find(text)]

  def find_at_start(self, text) -> list[RawParagraph]:
    return [x for x in self.items if isinstance(x, RawParagraph) and x.find_at_start(text)]

  def has_lists(self) -> bool:
    return len(self.lists()) > 0

  def has_content(self) -> bool:
    return not self.is_empty()

  def is_empty(self) -> bool:
    return len(self.items) == 0
  
  def _format_heading(self):
    if self.number and self.title:
      return f'<h{self.level}>{self.number} {self.title}</h{self.level}>'
    elif self.number:
      return f'<h{self.level}>{self.number}</h{self.level}>'
    elif self.title:
      return f'<h{self.level}>{self.title}</h{self.level}>'
    else:
      return ''
        
class Document():
  
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
