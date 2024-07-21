import json
from usdm_db import USDMDb
from model.file_import import FileImport
from model.files import Files

class USDMJson():

  def __init__(self, file_import: FileImport):
    files = Files(file_import.uuid)
    self._data = files.read(file_import.uuid, 'usdm')
    db = USDMDb()
    self._usdm = db.from_json(self._data)
    self._wrapper = self._usdm.wrapper()

  def study_version(self):
    # query = """
    #   MATCH (sv:StudyVersion {uuid: '%s'})
    #   WITH sv
    #   MATCH (sv)-[:TITLES_REL]->(st)-[:TYPE_REL]->(stc)
    #   MATCH (sv)-[:STUDY_IDENTIFIERS_REL]->(si)-[:STUDY_IDENTIFIER_SCOPE_REL]->(o:Organization)-[:ORGANIZATION_TYPE_REL]->(oc:Code)
    #   MATCH (sv)-[:STUDY_PHASE_REL]->(ac:AliasCode)-[:STANDARD_CODE_REL]->(pc:Code)
    #   MATCH (sv)-[]->(sd:StudyDesign)
    #   RETURN sv, st, stc, si, pc, o, oc, sd ORDER BY sv.version
    # """ % (self.uuid)
    return self._wrapper().study.versions[0]
