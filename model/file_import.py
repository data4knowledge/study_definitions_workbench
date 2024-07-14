from pydantic import BaseModel
from sqlalchemy.orm import Session
from model.file_import_db import get_import, get_import_by_uuid, create_import

class FileImportBase(BaseModel):
  filename: str
  filepath: str
  status: str

class FileImportCreate(FileImportBase):
  pass

class FileImport(FileImportBase):
  id: int
  uuid: str

  class Config:
    orm_mode = True

  @classmethod
  def find(cls, id: int, db: Session):
   return get_import(db, id)

  @classmethod
  def find_by_uuid(cls, uuid: str, db: Session):
   return get_import_by_uuid(db, uuid)

  @classmethod
  def create(cls, fullpath: str, filename: str, user_id: int, db: Session):
   return create_import(db, {'fullpath': fullpath, 'filename': filename}, user_id=user_id)
