import os
import re
import docx
import docx2txt
from pathlib import Path
from app.model.raw_docx.raw_document import RawDocument
from app.model.raw_docx.raw_section import RawSection
from app.model.raw_docx.raw_paragraph import RawParagraph
from app.model.raw_docx.raw_list import RawList
from app.model.raw_docx.raw_list_item import RawListItem
from app.model.raw_docx.raw_table import RawTable
from app.model.raw_docx.raw_table_row import RawTableRow
from app.model.raw_docx.raw_table_cell import RawTableCell
from app.model.raw_docx.raw_image import RawImage
from d4k_ms_base.logger import application_logger
from docx import Document as DocXProcessor
from docx.document import Document
from docx.oxml.table import CT_Tbl, CT_TcPr
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from lxml import etree


class RawDocx:
    class LogicError(Exception):
        pass

    def __init__(self, full_path: str):
        path = Path(full_path)
        # path.stem, path.suffix[1:]
        self.full_path = full_path
        self.dir = path.parent
        self.filename = path.name
        self.image_path = os.path.join(self.dir, "images")
        self.image_rels = {}
        self._organise_dir()
        # print(f"RAW DOCX: {self.full_path}, {self.dir}, {self.filename}, {self.image_path}")
        self.source_document = DocXProcessor(self.full_path)
        self.target_document = RawDocument()
        self._process()

    def _organise_dir(self):
        try:
            os.mkdir(self.image_path)
        except FileExistsError:
            pass
        except Exception as e:
            application_logger.exception("Failed to create image directory", e)

    def _process(self):
        # print(f"RAW DOCX: Process")
        try:
            self._extract_images()
            for block_item in self._iter_block_items(self.source_document):
                target_section = self.target_document.current_section()
                if isinstance(block_item, Paragraph):
                    self._process_paragraph(block_item, target_section, self.image_rels)
                elif isinstance(block_item, Table):
                    self._process_table(block_item, target_section)
                else:
                    application_logger.warning("Ignoring element")
                    raise ValueError
        except Exception as e:
            application_logger.exception("Exception raised processing document", e)

    def _extract_images(self):
        # Extract images to image dir
        docx2txt.process(self.full_path, self.image_path)
        # Save all 'rId:filenames' as references
        for r in self.source_document.part.rels.values():
            if isinstance(r._target, docx.parts.image.ImagePart):
                self.image_rels[r.rId] = os.path.join(
                    self.image_path, os.path.basename(r._target.partname)
                )

    def _iter_block_items(self, parent):
        """
        Yield each paragraph and table child within *parent*, in document
        order. Each returned value is an instance of either Table or
        Paragraph. *parent* would most commonly be a reference to a main
        Document object, but also works for a _Cell object, which itself can
        contain paragraphs and tables.
        """
        # print(f"ITERATION: {parent}")
        if isinstance(parent, Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("something's not right with the parent")

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)
            elif isinstance(child, etree._Element):
                if (
                    child.tag
                    == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcPr"
                ):
                    pass
                else:
                    # print(f"CHILD: {child.tag}")
                    application_logger.warning(f"Ignoring eTree element {child}")
            else:
                raise ValueError(f"something's not right with a child {type(child)}")

    def _process_table(self, table, target: RawSection | RawTableCell):
        target_table = RawTable()
        # print(f"TABLE: {type(target)}")
        target.add(target_table)
        for r_index, row in enumerate(table.rows):
            target_row = RawTableRow()
            target_table.add(target_row)
            cells = row.cells
            for c_index, cell in enumerate(cells):
                if cell._tc is not None:
                    x = cell._tc
                    r = x.right
                    l = x.left
                    t = x.top
                    try:
                        # Bottom method seems to have a bug.
                        # See https://github.com/python-openxml/python-docx/issues/1433
                        b = x.bottom
                    except Exception:
                        b = t + 1
                    h_span = r - l
                    v_span = b - t
                else:
                    h_span = 1
                    v_span = 1
                first = r_index == cell._tc.top and c_index == cell._tc.left
                target_cell = RawTableCell(h_span, v_span, first)
                # if target_cell.merged and target_cell.first:
                #   print(f"MERGED: {cell.text}, [{h_span}, {v_span}], {first}")
                target_row.add(target_cell)
                for block_item in self._iter_block_items(cell):
                    # print(f"CELL BLOCK: {type(block_item)}")
                    if isinstance(block_item, Paragraph):
                        self._process_cell(block_item, target_cell)
                    elif isinstance(block_item, Table):
                        raise self.LogicError("Table within table detected")
                        _process_table(block_item, target_cell)
                    elif isinstance(block_item, etree._Element):
                        # print(f"TAG: {block_item.tag}")
                        if block_item.tag == CT_TcPr:
                            pass
                        else:
                            application_logger.warning(
                                f"Ignoring eTree element {block_item}"
                            )
                    else:
                        raise self.LogicError(
                            f"something's not right with a child {type(block_item)}"
                        )

    def _process_cell(self, paragraph, target_cell: RawTableCell):
        if self._is_list(paragraph):
            list_level = self.get_list_level(paragraph)
            item = RawListItem(paragraph.text, list_level)
            if target_cell.is_in_list():
                # print(f"IN LIST:")
                list = target_cell.current_list()
            else:
                # print(f"NEW LIST:")
                list = RawList()
                target_cell.add(list)
            list.add(item)
            # print(f"List: <{paragraph.style.name}> <{list_level}> {paragraph.text}")
        else:
            target_paragraph = RawParagraph(paragraph.text)
            target_cell.add(target_paragraph)
            # for c in paragraph.text[0:2]:
            #  print(ord(c), hex(ord(c)), c.encode('utf-8'))
            # print(f"Text: <{paragraph.style.name}> {paragraph.text}")

    def _process_paragraph(
        self, paragraph, target_section: RawSection, image_rels: dict
    ):
        is_heading, level = self._is_heading(paragraph.style.name)
        if is_heading:
            target_section = RawSection(paragraph.text, paragraph.text, level)
            self.target_document.add(target_section)
        elif self._is_list(paragraph):
            list_level = self.get_list_level(paragraph)
            item = RawListItem(paragraph.text, list_level)
            if target_section.is_in_list():
                list = target_section.current_list()
            else:
                list = RawList()
                target_section.add(list)
            list.add(item)
        elif "Graphic" in paragraph._p.xml:
            for rId in image_rels:
                if rId in paragraph._p.xml:
                    target_image = RawImage(image_rels[rId])
                    target_section.add(target_image)
        else:
            target_paragraph = RawParagraph(paragraph.text)
            target_section.add(target_paragraph)

    def get_list_level(self, paragraph):
        list_level = paragraph._p.xpath("./w:pPr/w:numPr/w:ilvl/@w:val")
        return int(str(list_level[0])) if list_level else 0

    def _is_heading(self, text):
        if re.match(r"^\d\dHeading \d", text):
            try:
                level = int(text[0:2])
                return True, level
            except Exception:
                return True, 0
        if re.match(r"^Heading \d", text):
            try:
                level = int(text[8])
                return True, level
            except Exception:
                return True, 0
        return False, 0

    def _is_list(self, paragraph):
        level = paragraph._p.xpath("./w:pPr/w:numPr/w:ilvl/@w:val")
        if level:
            return True
        if paragraph.style.name in ["CPT_List Bullet", "List Bullet"]:
            return True
        if paragraph.text:
            # print(f"HEX: {hex(ord(paragraph.text[0]))}")
            if hex(ord(paragraph.text[0])) == "0x2022":
                return True
        return False
