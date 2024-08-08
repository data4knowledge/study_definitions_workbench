import os
from app.model import models
from app.model.database import engine
from app.model.models import Study as StudyDB, Version as VersionDB, FileImport as FileImportDB, Endpoint as EndpointDB
from app.model.models import UserEndpoint as UserEndpointDB, User as UserDB
from app.model.files import Files
from sqlalchemy.orm import Session
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Table, MetaData
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
      models.Base.metadata.create_all(bind=engine)
      application_logger.info("Database created")
      return True
    except FileExistsError as e:
      application_logger.info("Database dir exists")
      models.Base.metadata.create_all(bind=engine)
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
    self.session.commit()
    Files().delete_all()

  def clear_users(self):
    self.session.query(UserDB).delete()
    self.session.commit()
