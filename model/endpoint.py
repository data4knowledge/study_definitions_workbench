from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from model.models import Endpoint as EndpointDB

class EndpointBase(BaseModel):
  name: str
  endpoint: str
  type: str

class Endpoint(EndpointBase):
  id: int
  user_id: int

  class Config:
    from_attributes = True

  @classmethod
  def create(cls, name: str, endpoint: str, type: str, user_id: int, session: Session) -> 'Endpoint':
    data = {'name': name, 'endpoint': endpoint, 'type': type}
    db_item = EndpointDB(**data, user_id=user_id)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return cls(**db_item.__dict__)

  @classmethod
  def find(cls, id: int, session: Session) -> Optional['Endpoint']:
    db_item = session.query(EndpointDB).filter(EndpointDB.id == id).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def debug(cls, session: Session) -> list[dict]:
    count = session.query(EndpointDB).count()
    data = session.query(EndpointDB).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
      results[-1].pop('_sa_instance_state')
    result = {'items': results, 'count': count }
    return result

  @classmethod
  def page(cls, page: int, size: int, user_id: int, session: Session) -> list['Endpoint']:
    page = page if page >= 1 else 1
    size = size if size > 0 else 10
    skip = (page - 1) * size
    count = session.query(EndpointDB).filter(EndpointDB.user_id == user_id).count()
    data = session.query(EndpointDB).filter(EndpointDB.user_id == user_id).offset(skip).limit(size).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
    result = {'items': results, 'page': page, 'size': size, 'filter': '', 'count': count }
    return result


