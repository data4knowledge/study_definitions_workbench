import os
from app.model import database_tables
from app.model.database import engine
from app.model.database_tables import Study as StudyDB, Version as VersionDB, FileImport as FileImportDB, Endpoint as EndpointDB
from app.model.database_tables import UserEndpoint as UserEndpointDB, User as UserDB, TransmissionTable as TransmissionDB
from app.model.file_handling.data_files import DataFiles
from sqlalchemy.orm import Session
#from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Table, MetaData
from d4kms_generic.service_environment import ServiceEnvironment
from d4kms_generic import application_logger

class DatabaseManager():

  def __init__(self, session: Session):
    self.session = session

  @classmethod
  def check(cls):
    se = ServiceEnvironment()
    dir = se.get("DATABASE_PATH")
    application_logger.info("Checking database dir exists")
    try:
      os.mkdir(dir)
      application_logger.info("Database dir created")
      database_tables.Base.metadata.create_all(bind=engine)
      application_logger.info("Database created")
      return True
    except FileExistsError as e:
      application_logger.info("Database dir exists")
      database_tables.Base.metadata.create_all(bind=engine)
      return False
    except Exception as e:
      application_logger.exception(f"Exception checking/creating database dir '{dir}'", e)
      return False

  def clear_all(self):
    self.session.query(StudyDB).delete()
    self.session.query(VersionDB).delete()
    self.session.query(FileImportDB).delete()
    self.session.query(EndpointDB).delete()
    self.session.query(UserEndpointDB).delete()
    self.session.query(TransmissionDB).delete()
    self.session.commit()
    DataFiles().delete_all()

  def clear_users(self):
    self.session.query(UserDB).delete()
    self.session.commit()
