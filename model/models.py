from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):

  __tablename__ = "users"

  id = Column(Integer, primary_key=True)
  email = Column(String, unique=True, index=True)
  is_active = Column(Boolean, default=True)

  studies = relationship("Study", back_populates="owner")

class Study(Base):
    
  __tablename__ = "study"

  id = Column(Integer, primary_key=True)
  name = Column(String, index=True)
  owner_id = Column(Integer, ForeignKey("users.id"))

  owner = relationship("User", back_populates="studies")

