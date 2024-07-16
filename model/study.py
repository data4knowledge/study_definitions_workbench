from pydantic import BaseModel

class StudyBase(BaseModel):
  name: str

class StudyCreate(StudyBase):
  pass

class Study(StudyBase):
  id: int
  owner_id: int

  class Config:
    from_attributes = True

# from model.models import Study
# from sqlalchemy.orm import Session

# def get_studies(session: Session, skip: int = 0, limit: int = 100):
#   return session.query(Study).offset(skip).limit(limit).all()

# def create_study(session: Session, data: dict, user_id: int):
#   db_item = Study(**data, owner_id=user_id)
#   session.add(db_item)
#   session.commit()
#   session.refresh(db_item)
#   return db_item
