from typing import Optional
import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
from model.models import FileImport as FileImportDB

class FileImportBase(BaseModel):
  filepath: str
  filename: str
  type: str
  status: str
  uuid: str

class FileImport(FileImportBase):
  id: int
  user_id: int
  created: datetime.datetime

  class Config:
    from_attributes = True

  @classmethod
  def create(cls, fullpath: str, filename: str, status: str, type: str, uuid: str, user_id: int, session: Session) -> 'FileImport':
    data = {'filepath': fullpath, 'filename': filename, 'status': status, 'type': type, 'uuid': uuid}
    db_item = FileImportDB(**data, user_id=user_id)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return cls(**db_item.__dict__)

  @classmethod
  def find(cls, id: int, session: Session) -> Optional['FileImport']:
    db_item = session.query(FileImportDB).filter(FileImportDB.id == id).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def find_by_uuid(cls, uuid: str, session: Session) -> Optional['FileImport']:
    db_item = session.query(FileImportDB).filter(FileImportDB.uuid == uuid).first()
    return cls(**db_item.__dict__) if db_item else None  

  @classmethod
  def find_by_filename(cls, filename: str, session: Session) -> list['FileImport']:
    db_items = session.query(FileImportDB).filter(FileImportDB.filename == filename)
    results = []
    for db_item in db_items:
      results.append(cls(**db_item.__dict__))
    return results

  @classmethod
  def page(cls, page: int, size: int, user_id: int, session: Session) -> list[dict]:
    page = page if page >= 1 else 1
    size = size if size > 0 else 10
    skip = (page - 1) * size
    count = session.query(FileImportDB).filter(FileImportDB.user_id == user_id).count()
    data = session.query(FileImportDB).filter(FileImportDB.user_id == user_id).offset(skip).limit(size).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
    result = {'items': results, 'page': page, 'size': size, 'filter': '', 'count': count }
    return result

  @classmethod
  def debug(cls, session: Session) -> list[dict]:
    count = session.query(FileImportDB).count()
    data = session.query(FileImportDB).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
      results[-1]['created'] = results[-1]['created'].isoformat()
      results[-1].pop('_sa_instance_state')
    result = {'items': results, 'count': count }
    return result

  def update_status(self, status: str, session: Session) -> 'FileImport':
    #print(f"update_status: {status}")
    db_item = session.query(FileImportDB).filter(FileImportDB.id == self.id).first()
    db_item.status = status
    session.commit()
    session.refresh(db_item)
    return self.__class__(**db_item.__dict__)

