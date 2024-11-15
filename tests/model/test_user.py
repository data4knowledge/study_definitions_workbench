from app.model.user import User
#from app.model.database_tables import Study as StudyDB, Version as VersionDB, User as UserDB, FileImport as FileImportDB
#from sqlalchemy.orm import Session

def test_single_user(db):
  results = User.single_user()
  assert results == {'email': '', 'sub': 'SUE|1234567890', 'nickname': 'Single User', 'roles': []}
