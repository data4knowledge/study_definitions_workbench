from app.database.file_import import FileImport
from app.database.database_tables import (
    FileImport as FileImportDB,
    User as UserDB,
)
from sqlalchemy.orm import Session


def _clean(db: Session):
    db.query(FileImportDB).delete()
    db.query(UserDB).delete()
    db.commit()


def _setup_user(db: Session):
    user = UserDB(identifier="user_fi", email="fi@example.com", display_name="FI User")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_import(db: Session, user, index=1, uuid="uuid-1234"):
    return FileImport.create(
        fullpath=f"path/to/file{index}.xlsx",
        filename=f"file{index}.xlsx",
        status="success",
        type="USDM_EXCEL",
        uuid=uuid,
        user_id=user.id,
        session=db,
    )


def test_create(db):
    _clean(db)
    user = _setup_user(db)
    fi = _create_import(db, user)
    assert fi is not None
    assert fi.filename == "file1.xlsx"
    assert fi.type == "USDM_EXCEL"
    assert fi.user_id == user.id


def test_find_exists(db):
    _clean(db)
    user = _setup_user(db)
    fi = _create_import(db, user)
    found = FileImport.find(fi.id, db)
    assert found is not None
    assert found.id == fi.id


def test_find_not_exists(db):
    _clean(db)
    assert FileImport.find(99999, db) is None


def test_find_by_uuid(db):
    _clean(db)
    user = _setup_user(db)
    fi = _create_import(db, user, uuid="unique-uuid-abc")
    found = FileImport.find_by_uuid("unique-uuid-abc", db)
    assert found is not None
    assert found.uuid == "unique-uuid-abc"


def test_find_by_uuid_not_found(db):
    _clean(db)
    assert FileImport.find_by_uuid("nonexistent-uuid", db) is None


def test_find_by_filename(db):
    _clean(db)
    user = _setup_user(db)
    _create_import(db, user, index=1, uuid="a")
    _create_import(db, user, index=1, uuid="b")
    results = FileImport.find_by_filename("file1.xlsx", db)
    assert len(results) == 2


def test_find_by_filename_empty(db):
    _clean(db)
    results = FileImport.find_by_filename("nonexistent.xlsx", db)
    assert len(results) == 0


def test_page_first(db):
    _clean(db)
    user = _setup_user(db)
    for i in range(15):
        _create_import(db, user, index=i, uuid=f"uuid-{i}")
    result = FileImport.page(1, 10, user.id, db)
    assert result["count"] == 15
    assert len(result["items"]) == 10
    assert result["page"] == 1
    assert result["size"] == 10


def test_page_nth(db):
    _clean(db)
    user = _setup_user(db)
    for i in range(15):
        _create_import(db, user, index=i, uuid=f"uuid-{i}")
    result = FileImport.page(2, 10, user.id, db)
    assert result["count"] == 15
    assert len(result["items"]) == 5


def test_page_empty(db):
    _clean(db)
    user = _setup_user(db)
    result = FileImport.page(1, 10, user.id, db)
    assert result["count"] == 0
    assert len(result["items"]) == 0


def test_page_zero_values(db):
    _clean(db)
    user = _setup_user(db)
    _create_import(db, user, uuid="z1")
    result = FileImport.page(0, 0, user.id, db)
    assert result["page"] == 1
    assert result["size"] == 10


def test_debug(db):
    _clean(db)
    user = _setup_user(db)
    _create_import(db, user, uuid="d1")
    _create_import(db, user, index=2, uuid="d2")
    result = FileImport.debug(db)
    assert result["count"] == 2
    assert len(result["items"]) == 2
    assert "_sa_instance_state" not in result["items"][0]
    assert "created" in result["items"][0]


def test_delete_success(db):
    _clean(db)
    user = _setup_user(db)
    fi = _create_import(db, user, uuid="del1")
    result = fi.delete(db)
    assert result == 1
    assert FileImport.find(fi.id, db) is None


def test_delete_failure(db):
    _clean(db)
    user = _setup_user(db)
    fi = _create_import(db, user, uuid="del2")
    fi_id = fi.id
    fi.delete(db)
    # Try deleting again — record gone, should fail gracefully
    fi2 = FileImport(
        id=fi_id,
        user_id=user.id,
        filepath="x",
        filename="x",
        type="x",
        status="x",
        uuid="x",
        created=fi.created,
    )
    result = fi2.delete(db)
    assert result == 0


def test_update_status(db):
    _clean(db)
    user = _setup_user(db)
    fi = _create_import(db, user, uuid="upd1")
    assert fi.status == "success"
    updated = fi.update_status("completed", db)
    assert updated.status == "completed"
