import os
import re
import yaml
import json
import argparse
import docx2txt
import pandas as pd
from model.document.raw import *
from model.from_m11 import FromM11
from model.document.m11 import M11
from logger import application_logger
import docx
from docx import Document as DocXProcessor
from docx.document import Document
from docx.oxml.table import CT_Tbl, CT_TcPr
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from lxml import etree
from usdm_db import USDMDb, Wrapper

add_image = True

class LogicError(Exception):
  pass

def iter_block_items(parent):
  """
  Yield each paragraph and table child within *parent*, in document
  order. Each returned value is an instance of either Table or
  Paragraph. *parent* would most commonly be a reference to a main
  Document object, but also works for a _Cell object, which itself can
  contain paragraphs and tables.
  """
  if isinstance(parent, Document):
    parent_elm = parent.element.body
  elif isinstance(parent, _Cell):
    parent_elm = parent._tc
  else:
    raise ValueError(f"something's not right with the parent")

  for child in parent_elm.iterchildren():
    if isinstance(child, CT_P):
      yield Paragraph(child, parent)
    elif isinstance(child, CT_Tbl):
      yield Table(child, parent)
    elif isinstance(child, etree._Element):
      if child.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcPr':
        pass
      else:
        #print(f"CHILD: {child.tag}")
        application_logger.warning(f"Ignoring eTree element {child}")
    else:
      raise ValueError(f"something's not right with a child {type(child)}")

# def read_as_yaml_file(filepath):
#   with open(filepath, "r") as f:
#     data = yaml.load(f, Loader=yaml.FullLoader)
#   return data

# def save_as_yaml_file(data, filepath):
#   with open(filepath, 'w') as f:
#     yaml.dump(data, f, default_flow_style=False)

def save_as_html_file(data: str, filepath):
  with open(filepath, 'w') as f:
    f.write(data)

def save_as_json_file(data: str, filepath):
  with open(filepath, 'w', encoding='utf-8') as f:
    f.write(json.dumps(json.loads(data), indent=2))

def get_level(text):
  try:
    return int(text)
  except Exception as e:
    return 0
  
def process_table(table, target: RawSection | RawTableCell):
  target_table = RawTable()
  #print(f"TABLE: {type(target)}")
  target.add(target_table)
  for row in table.rows:
    target_row = RawTableRow()
    target_table.add(target_row)
    cells = row.cells
    for cell in cells:
      target_cell = RawTableCell()
      target_row.add(target_cell)
      for block_item in iter_block_items(cell):
        #print(f"CELL BLOCK: {type(block_item)}")
        if isinstance(block_item, Paragraph):
          process_cell(block_item, target_cell)
        elif isinstance(block_item, Table):
          raise LogicError(f"Table within table detected")
          process_table(block_item, target_cell)    
        elif isinstance(block_item, etree._Element):
          #print(f"TAG: {block_item.tag}")
          if block_item.tag == CT_TcPr:
            pass
          else:
            application_logger.warning(f"Ignoring eTree element {block_item}")
        else:
          raise LogicError(f"something's not right with a child {type(block_item)}")

def process_cell(paragraph, target_cell: RawTableCell):
  if is_list(paragraph):
    list_level = get_list_level(paragraph)
    item = RawListItem(paragraph.text, list_level)
    if target_cell.is_in_list():
      #print(f"IN LIST:")
      list = target_cell.current_list()
    else:
      #print(f"NEW LIST:")
      list = RawList()
      target_cell.add(list)
    list.add(item)
    #print(f"List: <{paragraph.style.name}> <{list_level}> {paragraph.text}")
  else:
    target_paragraph = RawParagraph(paragraph.text)
    target_cell.add(target_paragraph)
    #for c in paragraph.text[0:2]:
    #  print(ord(c), hex(ord(c)), c.encode('utf-8'))
    #print(f"Text: <{paragraph.style.name}> {paragraph.text}")

def process_paragraph(paragraph, target_section: RawSection, image_rels: dict):
  global add_image
  if is_heading(paragraph.style.name):
    level = get_level(paragraph.style.name[0:2])
    target_section = RawSection(paragraph.text, paragraph.text, level)
    target_document.add(target_section)
    #print(f"Heading: {paragraph.style.name} {paragraph.text}")
  elif is_list(paragraph):
    list_level = get_list_level(paragraph)
    #print(f"SECTION FOR LIST: {section.number}")
    item = RawListItem(paragraph.text, list_level)
    if target_section.is_in_list():
      #print(f"IN LIST:")
      list = target_section.current_list()
    else:
      #print(f"NEW LIST:")
      list = RawList()
      target_section.add(list)
    list.add(item)
    #print(f"List: <{paragraph.style.name}> <{list_level}> {paragraph.text}")
  elif 'Graphic' in paragraph._p.xml:
    #print(f"!!!!! Graphic !!!!!!")
    for rId in image_rels:
      if rId in paragraph._p.xml:
        target_image = RawImage(image_rels[rId])
        #if add_image:
        target_section.add(target_image)
        #  add_image = False
        # Your image will be in os.path.join(img_path, rels[rId])
  else:
    target_paragraph = RawParagraph(paragraph.text)
    target_section.add(target_paragraph)
    #for c in paragraph.text[0:2]:
    #  print(ord(c), hex(ord(c)), c.encode('utf-8'))
    #print(f"Text: <{paragraph.style.name}> {paragraph.text}")

def get_list_level(paragraph):
  list_level = paragraph._p.xpath("./w:pPr/w:numPr/w:ilvl/@w:val")
  return int(str(list_level[0])) if list_level else 0

def is_heading(text):
  return True if re.match("^\d\dHeading \d", text) else False

def is_list(paragraph):
  level = paragraph._p.xpath("./w:pPr/w:numPr/w:ilvl/@w:val")
  if level:
    return True
  if paragraph.style.name in ['CPT_List Bullet', 'List Bullet']:
    return True
  if paragraph.text:
    #print(f"HEX: {hex(ord(paragraph.text[0]))}")
    if hex(ord(paragraph.text[0])) == "0x2022":
      return True
  return False

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    prog='Import M11 Protocol Document Program',
    description='Will import a M11 Protocl Document into USDM',
    epilog='Note: Not that sophisticated! :)'
  )
  parser.add_argument('filename', help="The filename.") 
  dir = 'source_data'
  documents = [
    "ICH_M11_Template_ASP8062_Example.docx",
    "ICH_M11_Template_WA42380_Example.docx", 
    "ICH_M11_Template_DEUCRALIP_Example.docx",
    "ICH_M11_Template_IGBJ_Example.docx",
    "ICH_M11_Template_LZZT_Example.docx",
    "ICH_M11_Template_RadVax_Example.docx",
    "ICH_M11_Template_Test.docx",
  ]
  for item in documents:
    print(f"\n\nProcessing {item} ...")
    try:
      add_image = True
      file_root, file_extension = os.path.splitext(item)
      full_path = f"{dir}/{item}"
      #print(f"FILE: {file_root}, {file_extension}")
      #print(f"FILE: {full_path}")

      #image_path = os.path.join(dir, file_root)
      image_path = os.path.join(file_root)
      try:
        os.mkdir(image_path) 
      except FileExistsError as e:
        pass
      except Exception as e:
        application_logger.exception("Make directory error", e)
      docx2txt.process(full_path, image_path)
      document = DocXProcessor(full_path)

      # Save all 'rId:filenames' relationships in an dictionary named rels
      image_rels = {}
      for r in document.part.rels.values():
        if isinstance(r._target, docx.parts.image.ImagePart):
          image_rels[r.rId] = os.path.join(image_path, os.path.basename(r._target.partname))
          #print(f"IMAGE PATHNAME: {image_rels[r.rId]}")

      target_document = RawDocument()
      for block_item in iter_block_items(document):
        target_section = target_document.current_section()
        if isinstance(block_item, Paragraph):
          process_paragraph(block_item, target_section, image_rels)
        elif isinstance(block_item, Table):
          #print(f"TABLE!!!!")
          process_table(block_item, target_section)
        else:
          application_logger.warning(f"Ignoring element")
          raise ValueError
      
      df = pd.DataFrame.from_records([s.to_dict() for s in target_document.sections])
      df.to_excel(f'{file_root}.xlsx', index=False)

      full_text = ('\n').join([s.to_dict()['text'] for s in target_document.sections])
      save_as_html_file(full_text, f'{file_root}.html')

      m11 = M11(target_document)
      from_m11 = FromM11(m11)
      wrapper = from_m11.from_m11()
      save_as_json_file(wrapper.to_json(), f'{file_root}_usdm.json')
      usdm = USDMDb()
      usdm._wrapper = wrapper
      save_as_json_file(usdm.to_fhir(), f'{file_root}_fhir.json')

    except Exception as e:
      application_logger.exception(f"Exception raised processing '{item}'", e)
      print(f"Exception raised processing {item}, see logs for more details")

  print("Done")
    


