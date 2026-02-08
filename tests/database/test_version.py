from app.database.version import Version
from app.database.user import User
from app.database.study import Study
from app.database.database_tables import (
    Study as StudyDB,
    Version as VersionDB,
    User as UserDB,
    FileImport as FileImportDB,
)
from sqlalchemy.orm import Session


def test_page_empty(db):
    _clean(db)
    user, study = _base_setup(db)
    results = Version.page(1, 10, "", study.id, db)
    assert results["count"] == 0
    assert len(results["items"]) == 0


def test_page_first(db):
    _clean(db)
    user, study = _base_setup(db)
    _import_setup(db, 1, 1, user, study)
    results = Version.page(1, 10, "", study.id, db)
    assert results["count"] == 1
    assert len(results["items"]) == 1


def test_page_nth(db):
    _clean(db)
    user, study = _base_setup(db)
    _import_setup(db, 1, 15, user, study)
    results = Version.page(2, 10, "", study.id, db)
    assert results["count"] == 15
    assert len(results["items"]) == 5


def test_find_exists(db):
    _clean(db)
    user, study = _base_setup(db)
    _import_setup(db, 1, 1, user, study)
    versions = db.query(VersionDB).all()
    found = Version.find(versions[0].id, db)
    assert found is not None
    assert found.study_id == study.id


def test_find_not_exists(db):
    _clean(db)
    assert Version.find(99999, db) is None


def test_find_latest_version(db):
    _clean(db)
    user, study = _base_setup(db)
    _import_setup(db, 1, 3, user, study)
    latest = Version.find_latest_version(study.id, db)
    assert latest is not None


def test_find_latest_version_empty(db):
    _clean(db)
    user, study = _base_setup(db)
    latest = Version.find_latest_version(study.id, db)
    assert latest is None


def test_version_count(db):
    _clean(db)
    user, study = _base_setup(db)
    _import_setup(db, 1, 5, user, study)
    count = Version.version_count(study.id, db)
    assert count == 5


def test_debug(db):
    _clean(db)
    user, study = _base_setup(db)
    _import_setup(db, 1, 2, user, study)
    result = Version.debug(db)
    assert result["count"] == 2
    assert len(result["items"]) == 2
    assert "_sa_instance_state" not in result["items"][0]


def _clean(db: Session):
    db.query(UserDB).delete()
    db.query(StudyDB).delete()
    db.query(VersionDB).delete()
    db.query(FileImportDB).delete()
    db.commit()


def _base_setup(db: Session):
    user = UserDB(identifier="user_1", email="fred@example.com", display_name="fred")
    db.add(user)
    db.commit()
    db.refresh(user)
    study = StudyDB(
        name="STUDY",
        title="title",
        phase="phase",
        sponsor="sponsor",
        sponsor_identifier="sponsor_identifier",
        nct_identifier="nct_identifier",
        user_id=user.id,
    )
    db.add(study)
    db.commit()
    db.refresh(study)
    return user, study


def _import_setup(db: Session, base: int, count: int, user: User, study: Study):
    for index in range(count):
        item = base + index + 1
        file_import = FileImportDB(
            filepath=f"fullpath/filename{item}",
            filename=f"filename{item}",
            status="status",
            type="type",
            uuid="1234-5678-{item}",
            user_id=user.id,
        )
        db.add(file_import)
        db.commit()
        db.refresh(file_import)
        db_item = VersionDB(version="1", study_id=study.id, import_id=file_import.id)
        db.add(db_item)
        db.commit()
