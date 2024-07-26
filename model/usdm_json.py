import json
from model.file_import import FileImport
from model.files import Files
from model.version import Version
from sqlalchemy.orm import Session

class USDMJson():

  def __init__(self, id: int, session: Session):
    self.id = id
    version = Version.find(id, session)
    file_import = FileImport.find(version.import_id, session)
    self.uuid = file_import.uuid
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
      'id': self.id,
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
      result['study_designs'][design['id']] = {'id': design['name'], 'name': design['name'], 'label': design['label']}
    result['phase'] = version['studyPhase']
    return result

  def study_design_parameters(self, id: str):
      # query = """
      #   MATCH (sd:StudyDesign {uuid: '%s'})
      #   WITH sd
      #   MATCH (sd)-[:TRIAL_TYPES_REL]->(ttc:Code)
      #   MATCH (sd)-[:INTERVENTION_MODEL_REL]->(imc:Code)
      #   MATCH (sd)-[:TRIAL_INTENT_TYPES_REL]->(tic:Code)
      #   OPTIONAL MATCH (sd)-[:THERAPEUTIC_AREAS_REL]->(tac:Code)
      #   OPTIONAL MATCH (sd)-[:CHARACTERISTICS_REL]->(cc:Code)
      #   MATCH (sd)-[:POPULATION_REL]->(sdp:StudyDesignPopulation)
      #   OPTIONAL MATCH (sdp)-[:COHORTS_REL]->(coh:StudyCohort)
      #   RETURN sd, ttc, imc, tic, tac, cc, sdp, coh
      # """ % (self.uuid)
    design = next((x for x in self._data['study']['versions'][0]['studyDesigns'] if x['id'] == id), None)
    if design:
      result = {
        'id': self.id,
        'trial_types': {},
        'trial_intent': {},
        'intervention_models': {},
        'therapeutic_areas': {},
        'characteristics': {},
        'population':  None
      }
      result['trial_intent'][design['trialIntent']['decode']] = item['decode']
      for item in design['trialTypes']:
        result['trial_types'][item['decode']] = tt['decode']
      for item in design['intervention_models']:
        result['trial_types'][item['decode']] = item['decode']
      for item in design['characteristics']:
        result['trial_types'][item['decode']] = item['decode']
      return result
    else:
      return None
