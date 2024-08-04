from pydantic import BaseModel
from model.models import User as UserDB
from model.endpoint import Endpoint
from sqlalchemy.orm import Session

class UserBase(BaseModel):
  email: str
  display_name: str
  is_active: bool

class UserCreate(UserBase):
  pass

class User(UserBase):
  id: int
  
  class Config:
     from_attributes = True

  @classmethod
  def create(cls, email: str, display_name: str, session: Session):
    db_item = UserDB(email=email, display_name=display_name)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return cls(**db_item.__dict__)
  
  @classmethod
  def find(cls, id: int, session: Session):
    db_item = session.query(UserDB).filter(UserDB.id == id).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def find_by_email(cls, email: str, session: Session):
    db_item = session.query(UserDB).filter(UserDB.email == email).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def endpoints_page(cls, page: int, size: int, user_id: int, session: Session) -> list[dict]:
    page = page if page >= 1 else 1
    size = size if size > 0 else 10
    skip = (page - 1) * size
    user = session.query(UserDB).filter(UserDB.id == user_id).first()
    print(f"USER: {user}")
    count = len(user.endpoints)
    data = user.endpoints[skip:skip+size]
    print(f"USER: {count} {data}")
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
    result = {'items': results, 'page': page, 'size': size, 'filter': '', 'count': count }
    return result

  @classmethod
  def check(cls, info: dict, session: Session):
    present_in_db = True
    user = cls.find_by_email(info['email'], session)
    if not user:
      present_in_db = False
      user = cls.create(info['email'], info['nickname'], session)
    return user, present_in_db

  @classmethod
  def debug(cls, session: Session) -> list[dict]:
    count = session.query(UserDB).count()
    data = session.query(UserDB).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
      results[-1].pop('_sa_instance_state')
    result = {'items': results, 'count': count }
    return result

  def update_display_name(self, display_name: str, session: Session) -> 'User':
    db_item = session.query(UserDB).filter(UserDB.id == self.id).first()
    db_item.display_name = display_name
    session.commit()
    session.refresh(db_item)
    return self.__class__(**db_item.__dict__)