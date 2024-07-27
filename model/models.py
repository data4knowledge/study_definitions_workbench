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
  imports = relationship('FileImport', backref='user')
  studies = relationship('Study', backref='user')

class Study(Base):
    
  __tablename__ = "study"

  id = Column(Integer, primary_key=True)
  name = Column(String, index=True, nullable=False)
  title = Column(String, index=True, nullable=True)
  phase = Column(String, index=True, nullable=True)
  sponsor = Column(String, index=True, nullable=True)
  sponsor_identifier = Column(String, index=True, nullable=True)
  nct_identifier = Column(String, index=True, nullable=True)
  user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  versions = relationship('Version', backref='study')

class Version(Base):
    
  __tablename__ = "version"

  id = Column(Integer, primary_key=True)
  version = Column(Integer, index=True, nullable=False)
  study_id = Column(Integer, ForeignKey("study.id"), nullable=False)
  import_id = Column(Integer, ForeignKey("import.id"), nullable=False)
  
class FileImport(Base):
    
  __tablename__ = "import"

  id = Column(Integer, primary_key=True)
  uuid = Column(String, index=True, nullable=False)
  type = Column(String, nullable=False)
  created = Column(DateTime(timezone=True), default=func.now(), nullable=False)
  filepath = Column(String, nullable=False)
  filename = Column(String, nullable=False)
  status = Column(String, nullable=False)
  user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  version = relationship('Version', backref='file_import', uselist=False)
