from app.model.raw_docx.raw_docx import RawDocx
from usdm_model.wrapper import Wrapper
from usdm_excel.globals import Globals
from app.model.m11_protocol.m11_title_page import M11TitlePage
from app.model.m11_protocol.m11_inclusion_exclusion import M11InclusionExclusion
from app.model.m11_protocol.m11_sections import M11Sections
from app.model.m11_protocol.m11_to_usdm import M11ToUSDM
from app.model.m11_protocol.m11_styles import M11Styles
from app.model.m11_protocol.m11_estimands import M11IEstimands
from app.model.m11_protocol.m11_amendment import M11IAmendment
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
    self._estimands = M11IEstimands(self._raw_docx, self._globals)
    self._amendment = M11IAmendment(self._raw_docx, self._globals)
    self._sections = M11Sections(self._raw_docx, self._globals)
    self._styles = M11Styles(self._raw_docx, self._globals)

  async def process(self):
    self._styles.process()
    await self._title_page.process()
    self._inclusion_exclusion.process()
    self._estimands.process()
    self._amendment.process()
    self._sections.process()

  def to_usdm(self) -> Wrapper:
    usdm = M11ToUSDM(self._title_page, self._inclusion_exclusion, self._estimands, self._amendment, self._sections, self._globals, self._system_name, self._system_version)
    return usdm.export()

  def extra(self):
    return self._title_page.extra()
  