import re
from typing import Optional
from pydantic import BaseModel
from model.models import Study as StudyDB, Version as VersionDB
from model.version import Version
from model.user import User
from model.file_import import FileImport
from sqlalchemy.orm import Session

class StudyBase(BaseModel):
  name: str
  title: str
  phase: str
  sponsor: str
  sponsor_identifier: str
  nct_identifier: str

class StudyCreate(StudyBase):
  pass

class Study(StudyBase):
  id: int
  user_id: int
  
  class Config:
    from_attributes = True

  @classmethod
  def create(cls, name: str, title: str, phase: str, sponsor: str, sponsor_identifier: str, nct_identifier: str, session: Session) -> 'Study':
    db_item = StudyDB(name=name, title=title, phase=phase, sponsor=sponsor, sponsor_identifier=sponsor_identifier, nct_identifier=nct_identifier)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return cls(**db_item.__dict__)
  
  @classmethod
  def find(cls, id: int, session: Session) -> Optional['Study']:
    db_item = session.query(StudyDB).filter(StudyDB.id == id).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def find_by_name(cls, name: str, session: Session) -> Optional['Study']:
    db_item = session.query(StudyDB).filter(StudyDB.name == name).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def study_and_version(cls, parameters: dict, user: User, file_import: FileImport, session: Session) -> tuple['Study', bool]:
    present_in_db = True
    if not parameters['name']:
      parameters['name'] = cls._set_study_name(file_import)
    study = cls.find_by_name(parameters['name'], session)
    if not study:
      present_in_db = False
      study = StudyDB(
        name=parameters['name'], 
        title=parameters['full_title'], 
        phase=parameters['phase'], 
        sponsor=parameters['sponsor'], 
        sponsor_identifier=parameters['sponsor_identifier'], 
        nct_identifier=parameters['nct_identifier'],
        user_id=user.id
      )
      version = VersionDB(version=1, import_id=file_import.id)
      study.versions.append(version)
      session.add(study)
      session.commit()
      study = cls.find_by_name(parameters['name'], session)
    else:
      latest_version = Version.find_latest_version(study.id, session)
      version = latest_version.version + 1 if latest_version else 1
      new_version = VersionDB(version=version, study_id=study.id, import_id=file_import.id)
      session.add(new_version)
      session.commit()
    study = cls(**study.__dict__)
    return study, present_in_db

  @classmethod
  def page(cls, page: int, size: int, user_id: int, session: Session) -> list[dict]:
    page = page if page >= 1 else 1
    size = size if size > 0 else 10
    skip = (page - 1) * size
    count = session.query(StudyDB).filter(StudyDB.user_id == user_id).count()
    data = session.query(StudyDB).filter(StudyDB.user_id == user_id).offset(skip).limit(size).all()
    results = []
    for db_item in data:
      record = db_item.__dict__
      record['versions'] = Version.version_count(db_item.id, session)
      latest_version = Version.find_latest_version(record['id'], session)
      record['latest_version_id'] = latest_version.id
      record['import_type'] = FileImport.find(latest_version.import_id, session).type
      results.append(record)
    result = {'items': results, 'page': page, 'size': size, 'filter': '', 'count': count }
    return result

  @staticmethod
  def _set_study_name(file_import: FileImport) -> str:
    try:
      previous_imports = [x for x in FileImport.find_by_filename(file_import.filename) if x.uuid != file_import.uuid]
      studies = list(set([x.version.study_id for x in previous_imports]))
      return studies[0].name if len(studies) == 1 else Study._generate_name(file_import.filename)
    except:
      return Study._generate_name(file_import.filename)

  @staticmethod
  def _generate_name(filename: str) -> str:
    return re.sub('[\W_]+', '', filename.upper())
  