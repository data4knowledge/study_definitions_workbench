import os
from model.models import Study as StudyDB, Version as VersionDB, FileImport as FileImportDB
from model.user import User
from model.files import Files
from sqlalchemy.orm import Session
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
      return True
    except FileExistsError as e:
      application_logger.info("Database dir exists")
    except Exception as e:
      application_logger.exception(f"Exception checking/creating database dir '{dir}'", e)
      return False

  def clear_all(self):
    self.session.query(StudyDB).delete()
    self.session.query(VersionDB).delete()
    self.session.query(FileImportDB).delete()
    self.session.commit()
    Files().delete_all()

  def clear_by_user(self, user: User):
    pass

