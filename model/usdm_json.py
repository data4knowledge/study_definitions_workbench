import json
from usdm_db import USDMDb
from model.file_import import FileImport
from model.files import Files

class USDMJson():

  def __init__(self, file_import: FileImport):
    files = Files(file_import.uuid)
    f = open(files.path('usdm'))
    self._data = json.load(f)
    # self._db = USDMDb()
    # self._usdm = self._db.from_json(self._data)
    # self._wrapper = self._db.wrapper()

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
    #version = self._wrapper.study.versions[0]
    version = self._data['study']['versions'][0]
    result = {
      'identifiers': {},
      'titles': {},
      'study_designs': {},
      'phase': ''
    }
    for identifier in version['studyIdentifiers']:
      result['identifiers'][identifier['studyIdentifierScope']['organizationType']['decode']] = identifier
    for title in version['titles']:
      result['titles'][title['type']['decode']] = title['text']
    for design in version['studyDesigns']:
      result['study_designs'][design['id']] = {'name': design['name'], 'label': design['label']}
    result['phase'] = version['studyPhase']
    return result
