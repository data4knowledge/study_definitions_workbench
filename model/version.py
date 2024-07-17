from pydantic import BaseModel
from model.models import Version as VersionDB
from sqlalchemy.orm import Session
from sqlalchemy import desc

class VersionBase(BaseModel):
  version: int

class VersionCreate(VersionBase):
  pass

class Version(VersionBase):
  id: int
  study_id: int

  class Config:
    from_attributes = True

  @classmethod
  def create(cls, version: int, study_id: int, session: Session):
    db_item = VersionDB(version=version)
    session.add(**db_item, study_id=study_id)
    session.commit()
    session.refresh(db_item)
    return cls(**db_item.__dict__)
  
  @classmethod
  def find(cls, id: int, session: Session):
    db_item = session.query(VersionDB).filter(VersionDB.id == id).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def find_by_name(cls, name: str, session: Session):
    db_item = session.query(VersionDB).filter(VersionDB.name == name).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def find_latest_version(cls, study_id, session: Session):
    db_item = session.query(VersionDB).filter(VersionDB.study_id == study_id).order_by(desc(VersionDB.version)).first()
    return db_item.version if db_item else None

  @classmethod
  def version_count(cls, study_id, session: Session):
    return session.query(VersionDB).filter(VersionDB.study_id == study_id).count()
