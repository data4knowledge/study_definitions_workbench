from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.model.database_tables import UserEndpoint as UserEndpointDB

class UserEndpointBase(BaseModel):
  user_id: int
  endpoint_id: int

class UserEndpoint(UserEndpointBase):
  id: int

  class Config:
    from_attributes = True

  @classmethod
  def debug(cls, session: Session) -> list[dict]:
    count = session.query(UserEndpointDB).count()
    data = session.query(UserEndpointDB).all()
    #print(f"DEBUG: {data}")
    results = []
    for db_item in data:
      #print(f"DEBUG: {db_item}")
      results.append(db_item.__dict__)
      results[-1].pop('_sa_instance_state')
    result = {'items': results, 'count': count }
    return result



