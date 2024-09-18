#import re
#import dateutil.parser as parser
from app.model.raw_docx.raw_docx import RawDocx
#from app.model.raw_docx.raw_table import RawTable
from usdm_model.wrapper import Wrapper
from usdm_model.study import Study
from usdm_model.study_design import StudyDesign
from usdm_model.study_version import StudyVersion
from usdm_model.study_title import StudyTitle
from usdm_model.study_protocol_document import StudyProtocolDocument
from usdm_model.study_protocol_document_version import StudyProtocolDocumentVersion
#from usdm_model.code import Code
from usdm_model.study_identifier import StudyIdentifier
from usdm_model.organization import Organization
from usdm_model.address import Address
#from usdm_model.alias_code import AliasCode
from usdm_model.narrative_content import NarrativeContent
#from usdm_excel.id_manager import IdManager
#from usdm_excel.cdisc_ct_library import CDISCCTLibrary
#from usdm_excel.iso_3166 import ISO3166
from usdm_excel.globals import Globals
from uuid import uuid4
from usdm_info import __model_version__ as usdm_version, __package_version__ as system_version
from d4kms_generic import application_logger
#from app.utility.address_service import AddressService
from app.model.m11_protocol.m11_title_page import M11TitlePage
from app.model.m11_protocol.m11_inclusion_exclusion import M11InclusionExclusion
from app.model.m11_protocol.m11_sections import M11Sections
from app.model.m11_protocol.m11_to_usdm import M11ToUSDM
from app.model.m11_protocol.m11_styles import M11Styles
from app.model.m11_protocol.m11_utility import *

class M11Protocol():
  
  def __init__(self, filepath, system_name, system_version):
    self._globals = Globals()
    self._globals.create()
    self._system_name = system_name
    self._system_version = system_version
    self._raw_docx = RawDocx(filepath)
    self._id_manager = self._globals.id_manager
    self._cdisc_ct_manager = self._globals.cdisc_ct_library
    self._title_page = M11TitlePage(self._raw_docx, self._globals)
    self._inclusion_exclusion = M11InclusionExclusion(self._raw_docx, self._globals)
    self._sections = M11Sections(self._raw_docx, self._globals)
    self._styles = M11Styles(self._raw_docx, self._globals)

  async def process(self):
    self._styles.process()
    await self._title_page.process()
    self._inclusion_exclusion.process()
    self._sections.process()

  def to_usdm(self) -> Wrapper:
    usdm = M11ToUSDM(self._title_page, self._inclusion_exclusion, self._sections, self._globals, self._system_name, self._system_version)
    return usdm.export()

  def extra(self):
    return self._title_page.extra()
  