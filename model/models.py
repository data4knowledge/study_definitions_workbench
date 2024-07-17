import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from model.database import Base

class User(Base):

  __tablename__ = "user"

  id = Column(Integer, primary_key=True)
  email = Column(String, unique=True, index=True)
  is_active = Column(Boolean, default=True)

class Study(Base):
    
  __tablename__ = "study"

  id = Column(Integer, primary_key=True)
  name = Column(String, index=True)
  user_id = Column(Integer, ForeignKey("user.id"))

class Version(Base):
    
  __tablename__ = "version"

  id = Column(Integer, primary_key=True)
  version = Column(Integer, index=True)
  study_id = Column(Integer, ForeignKey("study.id"))
  version_id = Column(Integer, ForeignKey("version.id"))
  
class FileImport(Base):
    
  __tablename__ = "import"

  id = Column(Integer, primary_key=True)
  uuid = Column(String)
  type = Column(String)
  created = Column(DateTime(timezone=True), default=func.now())
  filepath = Column(String)
  status = Column(String)
  user_id = Column(Integer, ForeignKey("user.id"))
