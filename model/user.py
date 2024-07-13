from pydantic import BaseModel
from sqlalchemy.orm import Session
from model.user_db import get_user_by_email, create_user, get_user

class UserBase(BaseModel):
  email: str

class UserCreate(UserBase):
  pass

class User(UserBase):
  id: int
  is_active: bool

  class Config:
    orm_mode = True

  @classmethod
  def find(cls, id: int, db: Session):
   return get_user(db, id)

  @classmethod
  def find_by_email(cls, email: str, db: Session):
   return get_user_by_email(db, email)

  @classmethod
  def check(cls, email: str, db: Session):
    present_in_db = True
    user = get_user_by_email(db, email)
    if not user:
      present_in_db = False
      user = create_user(db, email)
    return user, present_in_db

