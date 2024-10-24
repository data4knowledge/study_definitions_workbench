import re
from sqlalchemy import text
from typing import Optional
from pydantic import BaseModel
from app.model.database_tables import Study as StudyDB, Version as VersionDB
from app.model.version import Version
from app.model.user import User
from app.model.file_import import FileImport
from sqlalchemy.orm import Session
from d4kms_generic import application_logger

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
  def find_by_name_and_user(cls, user: User, name: str, session: Session) -> Optional['Study']:
    db_item = session.query(StudyDB).filter(StudyDB.name == name, StudyDB.user_id == user.id).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def study_and_version(cls, parameters: dict, user: User, file_import: FileImport, session: Session) -> tuple['Study', bool]:
    present_in_db = True
    if not parameters['name']:
      parameters['name'] = cls._set_study_name(file_import)
    study = cls.find_by_name_and_user(user, parameters['name'], session)
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
      study = cls.find_by_name_and_user(user, parameters['name'], session)
    else:
      latest_version = Version.find_latest_version(study.id, session)
      version = latest_version.version + 1 if latest_version else 1
      new_version = VersionDB(version=version, study_id=study.id, import_id=file_import.id)
      session.add(new_version)
      session.commit()
    study = cls(**study.__dict__)
    return study, present_in_db

  @classmethod
  def summary(cls, id: int, session: Session) -> dict:
    db_item = session.query(StudyDB).filter(StudyDB.id == id).first()
    return cls._summary(db_item, session)

  @classmethod
  def page(cls, page: int, size: int, user_id: int, session: Session) -> list[dict]:
    page = page if page >= 1 else 1
    size = size if size > 0 else 10
    skip = (page - 1) * size
    count = session.query(StudyDB).filter(StudyDB.user_id == user_id).count()
    data = session.query(StudyDB).filter(StudyDB.user_id == user_id).offset(skip).limit(size).all()
    results = []
    for db_item in data:
      results.append(cls._summary(db_item, session))
    result = {'items': results, 'page': page, 'size': size, 'filter': '', 'count': count }
    return result

  @classmethod
  def debug(cls, session: Session) -> list[dict]:
    count = session.query(StudyDB).count()
    data = session.query(StudyDB).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
      results[-1].pop('_sa_instance_state')
    result = {'items': results, 'count': count }
    return result

  def delete(self, session: Session) -> int:
    try:
      record = session.query(StudyDB).filter(StudyDB.id == self.id).first()
      session.delete(record)
      session.commit()
      return 1
    except Exception as e:
      application_logger.exception(f"Failed to delete study record", e)
      return 0

  def file_imports(self, session: Session) -> dict:
    query = f"""
      SELECT i.* 
      FROM import i 
      JOIN version v ON i.id = v.import_id
      JOIN study s ON v.study_id = s.id
      WHERE s.id = {self.id}
    """
    results = session.execute(text(query))
    return results

  @staticmethod
  def _summary(item: StudyDB, session: Session) -> dict:
    record = item.__dict__
    record['versions'] = Version.version_count(item.id, session)
    latest_version = Version.find_latest_version(item.id, session)
    record['latest_version_id'] = latest_version.id
    record['import_type'] = FileImport.find(latest_version.import_id, session).type
    return record

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
  