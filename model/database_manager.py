from model.models import Study as StudyDB, Version as VersionDB, FileImport as FileImportDB
from model.file_import import FileImport
from model.version import Version
from model.study import Study
from model.user import User
from model.files import Files
from sqlalchemy.orm import Session

class DatabaseManager():

  def __init__(self, session: Session):
    self.session = session

  def clear_all(self):
    self.session.query(StudyDB).delete()
    self.session.query(VersionDB).delete()
    self.session.query(FileImportDB).delete()
    self.session.commit()
    Files().delete_all()

  def clear_by_user(self, user: User):
    pass

