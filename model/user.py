from pydantic import BaseModel
from sqlalchemy.orm import Session
from model.user_db import get_user_by_email, create_user

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
  def check(cls, email: str, db: Session):
    user = get_user_by_email(db, email)
    if not user:
      user = create_user(db, email)
    return user

