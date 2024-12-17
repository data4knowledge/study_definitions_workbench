from app.database.user import User
from app.database.study import Study
from app.database.database_tables import Study as StudyDB, Version as VersionDB, User as UserDB, FileImport as FileImportDB
from sqlalchemy.orm import Session

def test_page_empty(db):
  _clean(db)
  results = Study.page(1, 10, 1, {}, db)
  assert results['count'] == 0
  assert len(results['items']) == 0

def test_page_first(db):
  _clean(db)
  user = _base_setup(db)
  results = Study.page(1, 10, user.id, {}, db)
  assert results['count'] == 17
  assert len(results['items']) == 10

def test_page_nth(db):
  _clean(db)
  user = _base_setup(db)
  results = Study.page(2, 10, user.id, {}, db)
  assert results['count'] == 17
  assert len(results['items']) == 7

def test_page_filter_1(db):
  _clean(db)
  user = _base_setup(db)
  results = Study.page(1, 10, user.id, {'phase': ['Phase 2']}, db)
  assert results['count'] == 10
  assert len(results['items']) == 10

def test_page_filter_2(db):
  _clean(db)
  user = _base_setup(db)
  results = Study.page(1, 10, user.id, {'phase': ['Phase 2', 'Phase 3']}, db)
  assert results['count'] == 11
  assert len(results['items']) == 10

def test_page_filter_3(db):
  _clean(db)
  user = _base_setup(db)
  results = Study.page(1, 10, user.id, {'phase': ['Phase 2', 'Phase 3'], 'sponsor': ['SPONSOR B']}, db)
  assert results['count'] == 5
  assert len(results['items']) == 5

def test_phases(db):
  _clean(db)
  user = _base_setup(db)
  results = Study.phases(user.id, db)
  assert results == ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4']

def test_phases(db):
  _clean(db)
  user = _base_setup(db)
  results = Study.sponsors(user.id, db)
  assert results == ['SPONSOR A', 'SPONSOR B']

def _clean(db: Session):
  db.query(UserDB).delete()
  db.query(StudyDB).delete()
  db.query(VersionDB).delete()
  db.query(FileImportDB).delete()
  db.commit()

def _base_setup(db: Session):
  user = UserDB(identifier='user_1', email='fred@example.com', display_name='fred')
  db.add(user)
  db.commit()
  db.refresh(user)
  _setup_import(db, 1, 5, 'Phase 1', 'SPONSOR A', user)
  _setup_import(db, 6, 5, 'Phase 2', 'SPONSOR A', user)
  _setup_import(db, 11, 5, 'Phase 2', 'SPONSOR B', user)
  _setup_import(db, 16, 1, 'Phase 3', 'SPONSOR A', user)
  _setup_import(db, 17, 1, 'Phase 4', 'SPONSOR A', user)
  print(f"USER: {user.id}")
  return user

def _setup_import(db: Session, base: int, count: int, phase: str, sponsor: str, user: User):
  for index in range(count):
    item = base + index + 1
    print(f"ITEM: {item}, {base}, {count}, {phase}, {sponsor}")
    study = StudyDB(name=f'STUDY {item}', title=f'Study Title {item}', phase=phase, sponsor=sponsor, sponsor_identifier=f'sponsor_a_identifier_{item}', nct_identifier=f'nct_identifier_1{item}', user_id=user.id)
    db.commit()
    db.add(study)
    file_import = FileImportDB(filepath=f'fullpath/filename{item}', filename=f'filename{item}', status='status', type='type', uuid='1234-5678-{item}', user_id=user.id )
    db.add(file_import)
    db.commit()
    db.refresh(file_import)
    version = VersionDB(version='1', study_id=study.id, import_id=file_import.id)
    db.add(version)
    db.commit()
