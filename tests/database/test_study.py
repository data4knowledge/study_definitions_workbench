from app.database.user import User
from app.database.study import Study
from app.database.file_import import FileImport
from app.database.database_tables import (
    Study as StudyDB,
    Version as VersionDB,
    User as UserDB,
    FileImport as FileImportDB,
)
from sqlalchemy.orm import Session


def test_page_empty(db):
    _clean(db)
    results = Study.page(1, 10, 1, {}, db)
    assert results["count"] == 0
    assert len(results["items"]) == 0


def test_page_first(db):
    _clean(db)
    user = _base_setup(db)
    results = Study.page(1, 10, user.id, {}, db)
    assert results["count"] == 17
    assert len(results["items"]) == 10


def test_page_nth(db):
    _clean(db)
    user = _base_setup(db)
    results = Study.page(2, 10, user.id, {}, db)
    assert results["count"] == 17
    assert len(results["items"]) == 7


def test_page_filter_1(db):
    _clean(db)
    user = _base_setup(db)
    results = Study.page(1, 10, user.id, {"phase": ["Phase 2"]}, db)
    assert results["count"] == 10
    assert len(results["items"]) == 10


def test_page_filter_2(db):
    _clean(db)
    user = _base_setup(db)
    results = Study.page(1, 10, user.id, {"phase": ["Phase 2", "Phase 3"]}, db)
    assert results["count"] == 11
    assert len(results["items"]) == 10


def test_page_filter_3(db):
    _clean(db)
    user = _base_setup(db)
    results = Study.page(
        1, 10, user.id, {"phase": ["Phase 2", "Phase 3"], "sponsor": ["SPONSOR B"]}, db
    )
    assert results["count"] == 5
    assert len(results["items"]) == 5


def test_phases(db):
    _clean(db)
    user = _base_setup(db)
    results = Study.phases(user.id, db)
    assert results == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]


def test_sponsors(db):
    _clean(db)
    user = _base_setup(db)
    results = Study.sponsors(user.id, db)
    assert results == ["SPONSOR A", "SPONSOR B"]


def test_find_exists(db):
    _clean(db)
    user = _base_setup(db)
    items = db.query(StudyDB).all()
    study = Study.find(items[0].id, db)
    assert study is not None
    assert study.name == items[0].name


def test_find_not_exists(db):
    _clean(db)
    assert Study.find(99999, db) is None


def test_find_by_name_and_user(db):
    _clean(db)
    user = _base_setup(db)
    u = User(**user.__dict__)
    study = Study.find_by_name_and_user(u, "STUDY 2", db)
    assert study is not None
    assert study.name == "STUDY 2"


def test_find_by_name_and_user_not_found(db):
    _clean(db)
    user = _base_setup(db)
    u = User(**user.__dict__)
    study = Study.find_by_name_and_user(u, "NONEXISTENT", db)
    assert study is None


def test_study_and_version_new_study(db):
    _clean(db)
    user = _base_setup(db)
    u = User(**user.__dict__)
    fi = FileImportDB(
        filepath="path/new.xlsx",
        filename="new.xlsx",
        status="ok",
        type="USDM_EXCEL",
        uuid="uuid-new-study",
        user_id=user.id,
    )
    db.add(fi)
    db.commit()
    db.refresh(fi)
    fi_model = FileImport(**fi.__dict__)
    params = {
        "name": "BRAND_NEW",
        "full_title": "Brand New Study",
        "phase": "Phase 2",
        "sponsor": "SPONSOR Z",
        "sponsor_identifier": "sp_z",
        "nct_identifier": "nct_z",
    }
    study, present = Study.study_and_version(params, u, fi_model, db)
    assert study is not None
    assert present is False
    assert study.name == "BRAND_NEW"


def test_study_and_version_existing_study(db):
    _clean(db)
    user = _base_setup(db)
    u = User(**user.__dict__)
    fi = FileImportDB(
        filepath="path/exist.xlsx",
        filename="exist.xlsx",
        status="ok",
        type="USDM_EXCEL",
        uuid="uuid-exist",
        user_id=user.id,
    )
    db.add(fi)
    db.commit()
    db.refresh(fi)
    fi_model = FileImport(**fi.__dict__)
    params = {
        "name": "STUDY 2",
        "full_title": "Study Title 2",
        "phase": "Phase 1",
        "sponsor": "SPONSOR A",
        "sponsor_identifier": "sp_a",
        "nct_identifier": "nct_a",
    }
    study, present = Study.study_and_version(params, u, fi_model, db)
    assert study is not None
    assert present is True


def test_summary(db):
    _clean(db)
    user = _base_setup(db)
    items = db.query(StudyDB).all()
    result = Study.summary(items[0].id, db)
    assert "versions" in result
    assert "latest_version_id" in result
    assert "import_type" in result


def test_delete_success(db):
    _clean(db)
    user = _base_setup(db)
    items = db.query(StudyDB).all()
    study = Study(**items[0].__dict__)
    result = study.delete(db)
    assert result == 1


def test_delete_failure(db):
    _clean(db)
    study = Study(
        id=99999, user_id=1, name="X", title="X", phase="X",
        sponsor="X", sponsor_identifier="X", nct_identifier="X",
    )
    result = study.delete(db)
    assert result == 0


def test_debug(db):
    _clean(db)
    user = _base_setup(db)
    result = Study.debug(db)
    assert result["count"] == 17
    assert len(result["items"]) == 17
    assert "_sa_instance_state" not in result["items"][0]


def test_study_and_version_no_name(db):
    _clean(db)
    user = _base_setup(db)
    u = User(**user.__dict__)
    fi = FileImportDB(
        filepath="path/noname.xlsx",
        filename="noname.xlsx",
        status="ok",
        type="USDM_EXCEL",
        uuid="uuid-noname",
        user_id=user.id,
    )
    db.add(fi)
    db.commit()
    db.refresh(fi)
    fi_model = FileImport(**fi.__dict__)
    params = {
        "name": "",
        "full_title": "No Name Study",
        "phase": "Phase 1",
        "sponsor": "SPONSOR A",
        "sponsor_identifier": "sp_a",
        "nct_identifier": "nct_a",
    }
    study, present = Study.study_and_version(params, u, fi_model, db)
    assert study is not None
    assert present is False


def test_generate_name():
    assert Study._generate_name("my_file-v2.xlsx") == "MYFILEV2XLSX"
    assert Study._generate_name("simple") == "SIMPLE"


def test_add_filters_name_like(db):
    _clean(db)
    user = _base_setup(db)
    query = db.query(StudyDB)
    query = Study._add_filters(query, {"name": "STUDY 2"})
    results = query.all()
    assert len(results) == 1


def test_add_filters_other(db):
    _clean(db)
    user = _base_setup(db)
    query = db.query(StudyDB)
    query = Study._add_filters(query, {"user_id": user.id})
    results = query.all()
    assert len(results) == 17


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
    _setup_import(db, 1, 5, "Phase 1", "SPONSOR A", user)
    _setup_import(db, 6, 5, "Phase 2", "SPONSOR A", user)
    _setup_import(db, 11, 5, "Phase 2", "SPONSOR B", user)
    _setup_import(db, 16, 1, "Phase 3", "SPONSOR A", user)
    _setup_import(db, 17, 1, "Phase 4", "SPONSOR A", user)
    print(f"USER: {user.id}")
    return user


def _setup_import(
    db: Session, base: int, count: int, phase: str, sponsor: str, user: User
):
    for index in range(count):
        item = base + index + 1
        print(f"ITEM: {item}, {base}, {count}, {phase}, {sponsor}")
        study = StudyDB(
            name=f"STUDY {item}",
            title=f"Study Title {item}",
            phase=phase,
            sponsor=sponsor,
            sponsor_identifier=f"sponsor_a_identifier_{item}",
            nct_identifier=f"nct_identifier_1{item}",
            user_id=user.id,
        )
        db.commit()
        db.add(study)
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
        version = VersionDB(version="1", study_id=study.id, import_id=file_import.id)
        db.add(version)
        db.commit()
