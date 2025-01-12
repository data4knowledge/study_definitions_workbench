from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserEndpoint(Base):
    __tablename__ = "user_endpoint"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    endpoint_id = Column(Integer, ForeignKey("endpoint.id"))


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    identifier = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, index=True)
    display_name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    imports = relationship("FileImport", backref="user")
    studies = relationship("Study", backref="user")
    transmissions = relationship("TransmissionTable", backref="user")
    endpoints = relationship("Endpoint", secondary="user_endpoint", backref="user")


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
    versions = relationship("Version", backref="study", cascade="all, delete")


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
    version = relationship(
        "Version", backref="file_import", uselist=False, cascade="all, delete"
    )


class TransmissionTable(Base):
    __tablename__ = "transmission"

    id = Column(Integer, primary_key=True)
    created = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    status = Column(String, nullable=False)
    study = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)


class Endpoint(Base):
    __tablename__ = "endpoint"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    endpoint = Column(String, unique=True, nullable=False)
