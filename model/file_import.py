from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4
from model.models import FileImport as FileImportDB

class FileImportBase(BaseModel):
  filename: str
  filepath: str
  status: str
  uuid: str

class FileImport(FileImportBase):
  id: int

  class Config:
    from_attributes = True

  @classmethod
  def create(cls, fullpath: str, filename: str, status: str, user_id: int, session: Session) -> 'FileImport':
    data = {'filepath': fullpath, 'filename': filename, 'status': status, 'uuid': str(uuid4())}
    db_item = FileImportDB(**data, owner_id=user_id)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return cls(**db_item.__dict__)

  @classmethod
  def find(cls, id: int, session: Session) -> 'FileImport':
    db_item = session.query(FileImportDB).filter(FileImportDB.id == id).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def find_by_uuid(cls, uuid: str, session: Session) -> 'FileImport':
    db_item = session.query(FileImportDB).filter(FileImportDB.uuid == uuid).first()
    return cls(**db_item.__dict__) if db_item else None  

  @classmethod
  def list(cls, session: Session, page: int=1, size: int=10):
    page = page if page >= 1 else 1
    size = size if size > 0 else 10
    skip = (page - 1) * size
    count = session.query(FileImportDB).count()
    print(f"list: {count}, {page}, {size}, {skip}")
    data = session.query(FileImportDB).offset(skip).limit(size).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
    result = {'items': results, 'page': page, 'size': size, 'filter': '', 'count': count }
    print(f"list: {result}")
    return result
  
  def update_status(self, status: str, session: Session) -> 'FileImport':
    print(f"update_status: {status}")
    db_item = session.query(FileImportDB).filter(FileImportDB.id == self.id).first()
    db_item.status = status
    session.commit()
    session.refresh(db_item)
    return self.__class__(**db_item.__dict__)

