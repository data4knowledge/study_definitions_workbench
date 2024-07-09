from model.models import Study
from sqlalchemy.orm import Session

def get_studies(db: Session, skip: int = 0, limit: int = 100):
  return db.query(Study).offset(skip).limit(limit).all()

def create_study(db: Session, data: dict, user_id: int):
  db_item = Study(**data, owner_id=user_id)
  db.add(db_item)
  db.commit()
  db.refresh(db_item)
  return db_item