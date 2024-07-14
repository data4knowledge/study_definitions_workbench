from model.models import FileImport
from sqlalchemy.orm import Session
from uuid import uuid4

def get_file_import(db: Session, import_id: int):
  return db.query(FileImport).filter(FileImport.id == import_id).first()

def get_file_import_by_uuid(db: Session, uuid: str):
  return db.query(FileImport.filter(FileImport.uuid == uuid)).first()

def get_file_imports(db: Session, skip: int = 0, limit: int = 100):
  return db.query(FileImport).offset(skip).limit(limit).all()

def create_file_import(db: Session, data: dict, user_id: int):
  data['uuid'] = str(uuid4())
  db_item = FileImport(**data, owner_id=user_id)
  db.add(db_item)
  db.commit()
  db.refresh(db_item)
  return db_item