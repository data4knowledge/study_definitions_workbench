from model.models import User
from sqlalchemy.orm import Session

def get_user(db: Session, user_id: int):
  return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
  return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
  return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, email: str):
  db_user = User(email=email)
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user