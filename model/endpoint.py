from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from model.models import Endpoint as EndpointDB
from model.models import UserEndpoint as UserEndpointDB
from model.models import User as UserDB

class EndpointBase(BaseModel):
  name: str
  endpoint: str
  type: str

class Endpoint(EndpointBase):
  id: int

  class Config:
    from_attributes = True

  @classmethod
  def create(cls, name: str, endpoint: str, type: str, user_id: int, session: Session) -> 'Endpoint':
    db_item  = session.query(EndpointDB).filter(EndpointDB.endpoint == endpoint).first()
    user = session.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_item:
      data = {'name': name, 'endpoint': endpoint, 'type': type}
      db_item = EndpointDB(**data)
      session.add(db_item)
    user.endpoints.append(db_item)
    session.add(user)
    session.commit()
    session.refresh(db_item)
    return cls(**db_item.__dict__)

  @classmethod
  def find_by_endpoint(cls, endpoint: str, session: Session):
    db_item = session.query(EndpointDB).filter(EndpointDB.endpoint == endpoint).first()
    return cls(**db_item.__dict__) if db_item else None

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

  def delete(self, user_id: int, session: Session) -> int:
    endpoint = session.query(EndpointDB).filter(EndpointDB.id == self.id).first()
    user = session.query(UserDB).filter(UserDB.id == user_id).first()
    user.endpoints.remove(endpoint)
    user_endpoint = session.query(UserEndpointDB).filter(UserEndpointDB.endpoint_id == endpoint.id).all()
    if len(user_endpoint) == 0:
      endpoint.delete()
    session.commit()
    return 1
