from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):

  __tablename__ = "user"

  id = Column(Integer, primary_key=True)
  email = Column(String, unique=True, index=True)
  is_active = Column(Boolean, default=True)

  studies = relationship("Study", back_populates="study_owner")
  imports = relationship("FileImport", back_populates="study_owner")

class Study(Base):
    
  __tablename__ = "study"

  id = Column(Integer, primary_key=True)
  name = Column(String, index=True)
  owner_id = Column(Integer, ForeignKey("user.id"))

  versions = relationship("Version", back_populates="version_owner")
  study_owner = relationship("User", back_populates="studies")

class Version(Base):
    
  __tablename__ = "version"

  id = Column(Integer, primary_key=True)
  name = Column(String, index=True)
  owner_id = Column(Integer, ForeignKey("study.id"))

  version_owner = relationship("Study", back_populates="versions")

class FileImport(Base):
    
  __tablename__ = "import"

  id = Column(Integer, primary_key=True)
  uuid = Column(String)
  filename = Column(String)
  filepath = Column(String)
  status = Column(String)
  owner_id = Column(Integer, ForeignKey("user.id"))

  study_owner = relationship("User", back_populates="imports")
