from pydantic import BaseModel
from model.models import Study as StudyDB, Version as VersionDB
from model.version import Version
from sqlalchemy.orm import Session

class StudyBase(BaseModel):
  name: str

class StudyCreate(StudyBase):
  pass

class Study(StudyBase):
  id: int
  user_id: int

  class Config:
    from_attributes = True

  @classmethod
  def create(cls, name: str, session: Session):
    db_item = StudyDB(name=name)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return cls(**db_item.__dict__)
  
  @classmethod
  def find(cls, id: int, session: Session):
    db_item = session.query(StudyDB).filter(StudyDB.id == id).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def find_by_name(cls, name: str, session: Session):
    db_item = session.query(StudyDB).filter(StudyDB.name == name).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def study_and_version(cls, name: str, user_id: int, import_id: int, session: Session):
    present_in_db = True
    study = cls.find_by_name(name, session)
    if not study:
      present_in_db = False
      study = StudyDB(name=name, user_id=user_id)
      version = VersionDB(version=1, import_id=import_id)

      study.versions.append(version)
      session.add(study)

      session.commit()
      study = cls.find_by_name(name, session)
    else:
      latest_version = Version.find_latest_version(study.id, session)
      version = latest_version + 1 if latest_version else 1
      new_version = VersionDB(version=version, study_id=study.id, import_id=import_id)
      session.add(new_version)
      session.commit()
    study = cls(**study.__dict__)
    return study, present_in_db
