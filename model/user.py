from pydantic import BaseModel
from model.models import User as UserDB
from sqlalchemy.orm import Session

class UserBase(BaseModel):
  email: str
  is_active: bool

class UserCreate(UserBase):
  pass

class User(UserBase):
  id: int
  
  class Config:
     from_attributes = True

  @classmethod
  def create(cls, email: str, session: Session):
    db_item = UserDB(email=email)
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
  def debug(cls, session: Session) -> list[dict]:
    count = session.query(UserDB).count()
    data = session.query(UserDB).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
      results[-1].pop('_sa_instance_state')
    result = {'items': results, 'count': count }
    return result

  @classmethod
  def check(cls, email: str, session: Session):
    present_in_db = True
    user = cls.find_by_email(email, session)
    if not user:
      present_in_db = False
      user = cls.create(email, session)
    return user, present_in_db

# def get_users(session: Session, skip: int = 0, limit: int = 100):
#   return session.query(User).offset(skip).limit(limit).all()
