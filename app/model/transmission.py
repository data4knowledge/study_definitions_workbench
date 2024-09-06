from pydantic import BaseModel
from app.model.database_tables import TransmissionTable
from sqlalchemy.orm import Session
from sqlalchemy import desc

class TransmissionBase(BaseModel):
  version: int
  study: str
  status: str

class Transmission(TransmissionBase):
  id: int
  user_id: int

  class Config:
    from_attributes = True

  @classmethod
  def create(cls, version: int, study: str, status: str, user_id: int, session: Session) -> 'Transmission':
    data = {'version': version, 'study': study, 'status': status}
    db_item = TransmissionTable(**data, user_id=user_id)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return cls(**db_item.__dict__)
  
  @classmethod
  def find(cls, id: int, session: Session) -> 'Transmission':
    db_item = session.query(TransmissionTable).filter(TransmissionTable.id == id).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def page(cls, page: int, size: int, user_id: int, session: Session) -> list[dict]:
    page = page if page >= 1 else 1
    size = size if size > 0 else 10
    skip = (page - 1) * size
    count = session.query(TransmissionTable).filter(TransmissionTable.user_id == user_id).count()
    data = session.query(TransmissionTable).filter(TransmissionTable.user_id == user_id).offset(skip).limit(size).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
    result = {'items': results, 'page': page, 'size': size, 'filter': '', 'count': count }
    return result

  @classmethod
  def debug(cls, session: Session) -> list[dict]:
    count = session.query(TransmissionTable).count()
    data = session.query(TransmissionTable).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
      results[-1].pop('_sa_instance_state')
    result = {'items': results, 'count': count }
    return result

  def update_status(self, status: str, session: Session) -> 'Transmission':
    print(f"update_status: {status}")
    db_item = session.query(TransmissionTable).filter(TransmissionTable.id == self.id).first()
    db_item.status = status
    session.commit()
    session.refresh(db_item)
    return self.__class__(**db_item.__dict__)

