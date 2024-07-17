from pydantic import BaseModel
from model.models import Version as VersionDB
from sqlalchemy.orm import Session

class VersionBase(BaseModel):
  version: int

class VersionCreate(VersionBase):
  pass

class Version(VersionBase):
  id: int
  user_id: int
  study_id: int

  class Config:
    from_attributes = True

  @classmethod
  def create(cls, name: str, study_id, int, user_id: int, session: Session):
    db_item = VersionDB(name=name)
    session.add(**db_item, study_id=study_id, user_id=user_id)
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
  def check(cls, name: str, session: Session):
    present_in_db = True
    item = cls.find_by_name(name, session)
    if not item:
      present_in_db = False
      user = cls.create(name, session)
    return item, present_in_db
