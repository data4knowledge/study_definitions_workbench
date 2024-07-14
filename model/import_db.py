from model.models import Import
from sqlalchemy.orm import Session

def get_imports(db: Session, skip: int = 0, limit: int = 100):
  return db.query(Import).offset(skip).limit(limit).all()

def create_import(db: Session, data: dict, user_id: int):
  db_item = Import(**data, owner_id=user_id)
  db.add(db_item)
  db.commit()
  db.refresh(db_item)
  return db_item