from unittest.mock import patch

from app.database.database_manager import DatabaseManager
from app.database.database_tables import (
    Endpoint as EndpointDB,
)
from app.database.database_tables import (
    FileImport as FileImportDB,
)
from app.database.database_tables import (
    Study as StudyDB,
)
from app.database.database_tables import (
    TransmissionTable as TransmissionDB,
)
from app.database.database_tables import (
    User as UserDB,
)
from app.database.database_tables import (
    UserEndpoint as UserEndpointDB,
)
from app.database.database_tables import (
    Version as VersionDB,
)
from app.model.file_handling.data_files import DataFiles


def test_init():
    """Test initialization of DatabaseManager."""
    manager = DatabaseManager()
    assert manager.session is not None


@patch("os.mkdir")
@patch("app.database.database_tables.Base.metadata.create_all")
def test_check_dir_created(mock_create_all, mock_mkdir):
    """Test check method when directory doesn't exist."""
    mock_mkdir.return_value = None
    result = DatabaseManager().check()
    assert result is True
    mock_mkdir.assert_called_once()
    mock_create_all.assert_called_once()


@patch("os.mkdir")
@patch("app.database.database_tables.Base.metadata.create_all")
def test_check_dir_exists(mock_create_all, mock_mkdir):
    """Test check method when directory already exists."""
    mock_mkdir.side_effect = FileExistsError()
    result = DatabaseManager().check()
    assert result is False
    mock_mkdir.assert_called_once()
    mock_create_all.assert_called_once()


@patch("os.mkdir")
@patch("app.database.database_tables.Base.metadata.create_all")
def test_check_exception(mock_create_all, mock_mkdir):
    """Test check method when an exception occurs."""
    mock_mkdir.side_effect = Exception("Test exception")
    result = DatabaseManager().check()
    assert result is False
    mock_mkdir.assert_called_once()
    mock_create_all.assert_not_called()


def _clean_db(db):
    """Clean the database before tests."""
    db.query(UserDB).delete()
    db.query(StudyDB).delete()
    db.query(VersionDB).delete()
    db.query(FileImportDB).delete()
    db.query(EndpointDB).delete()
    db.query(UserEndpointDB).delete()
    db.query(TransmissionDB).delete()
    db.commit()


def test_clear_all(db):
    """Test clear_all method."""
    # Clean the database first
    _clean_db(db)

    # Setup - add some data to the database
    user = UserDB(
        identifier="user_clear_all",
        email="test_clear_all@example.com",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    study = StudyDB(
        name="Test Study",
        title="Test Study Title",
        phase="Phase 1",
        sponsor="Test Sponsor",
        sponsor_identifier="TST-123",
        nct_identifier="NCT12345678",
        user_id=user.id,
    )
    db.add(study)
    db.commit()

    # Verify data was added
    users_before = db.query(UserDB).count()
    assert users_before > 0
    assert db.query(StudyDB).count() > 0

    # Execute clear_all with a mock for DataFiles().delete_all()
    with patch.object(DataFiles, "delete_all") as mock_delete_all:
        manager = DatabaseManager()
        manager.clear_all()

        # Verify all data tables were cleared
        assert db.query(StudyDB).count() == 0
        assert db.query(VersionDB).count() == 0
        assert db.query(FileImportDB).count() == 0
        assert db.query(EndpointDB).count() == 0
        assert db.query(UserEndpointDB).count() == 0
        assert db.query(TransmissionDB).count() == 0

        # The user table MUST be preserved — it is the login allow-list
        # and holds roles. clear_all must never touch it.
        assert db.query(UserDB).count() == users_before

        # Verify DataFiles.delete_all was called
        mock_delete_all.assert_called_once()


def test_clear_users(db):
    """Test clear_users method."""
    # Clean the database first
    _clean_db(db)

    # Setup - add a user to the database
    user = UserDB(
        identifier="user_clear_users",
        email="test_clear_users@example.com",
        display_name="Test User",
    )
    db.add(user)
    db.commit()

    # Verify user was added
    assert db.query(UserDB).count() > 0

    # Execute clear_users
    manager = DatabaseManager()
    manager.clear_users()

    # Verify users were cleared
    assert db.query(UserDB).count() == 0


def test_migrate_below_31(db):
    """Test migration when version < 31."""
    manager = DatabaseManager(session=db)
    # Set version to 0
    cursor = db.connection().connection.cursor()
    cursor.execute("pragma user_version = 0")
    db.commit()
    manager.migrate()
    # A single migrate() call applies every pending step up to the latest.
    version = manager._get_version()
    assert version == 34
    cursor = db.connection().connection.cursor()
    cols = [row[1] for row in cursor.execute("pragma table_info(user)")]
    assert "roles" in cols


def test_migrate_at_31(db):
    """Test migration when version == 31 runs through to the latest version."""
    manager = DatabaseManager(session=db)
    cursor = db.connection().connection.cursor()
    cursor.execute("pragma user_version = 31")
    db.commit()
    manager.migrate()
    version = manager._get_version()
    assert version == 34


def test_migrate_at_32(db):
    """Test migration when version == 32 (adds roles column, runs to latest)."""
    manager = DatabaseManager(session=db)
    cursor = db.connection().connection.cursor()
    cursor.execute("pragma user_version = 32")
    db.commit()
    manager.migrate()
    version = manager._get_version()
    assert version == 34
    # The user table must have a roles column after this migration.
    cols = [row[1] for row in cursor.execute("pragma table_info(user)")]
    assert "roles" in cols


def _add_import(db, user_id, study_id, type, uuid, version=1):
    file_import = FileImportDB(
        uuid=uuid,
        type=type,
        filepath="path",
        filename="file.json",
        status="Successful",
        user_id=user_id,
    )
    db.add(file_import)
    db.commit()
    db.refresh(file_import)
    db.add(VersionDB(version=version, study_id=study_id, import_id=file_import.id))
    db.commit()
    return file_import.id


def _add_study(db, user_id, name):
    study = StudyDB(name=name, user_id=user_id)
    db.add(study)
    db.commit()
    db.refresh(study)
    return study.id


def test_migrate_at_33_drops_prism2_imports(db):
    """v33 -> v34 deletes PRISM2 imports, their versions and files, and any
    study left with no versions. Other imports and studies are kept."""
    _clean_db(db)
    user = UserDB(
        identifier="user_migrate_34",
        email="test_migrate_34@example.com",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    only_prism2 = _add_study(db, user.id, "Only PRISM2")
    mixed = _add_study(db, user.id, "Mixed")
    p2_a = _add_import(db, user.id, only_prism2, "FHIR_PRISM2_JSON", "uuid-p2-a")
    p2_b = _add_import(db, user.id, mixed, "FHIR_PRISM2_JSON", "uuid-p2-b")
    m11 = _add_import(db, user.id, mixed, "M11_DOCX", "uuid-m11", version=2)

    manager = DatabaseManager(session=db)
    cursor = db.connection().connection.cursor()
    cursor.execute("pragma user_version = 33")
    db.commit()
    with patch.object(DataFiles, "delete") as mock_delete:
        manager.migrate()
        assert mock_delete.call_count == 2

    assert manager._get_version() == 34
    db.expire_all()
    assert db.query(StudyDB).filter(StudyDB.id == only_prism2).count() == 0
    assert db.query(StudyDB).filter(StudyDB.id == mixed).count() == 1
    remaining = [i.id for i in db.query(FileImportDB).all()]
    assert p2_a not in remaining
    assert p2_b not in remaining
    assert m11 in remaining
    versions = db.query(VersionDB).filter(VersionDB.study_id == mixed).all()
    assert [v.import_id for v in versions] == [m11]


def test_migrate_at_33_no_prism2_imports(db):
    """v33 -> v34 with no PRISM2 imports changes nothing but the version."""
    _clean_db(db)
    manager = DatabaseManager(session=db)
    cursor = db.connection().connection.cursor()
    cursor.execute("pragma user_version = 33")
    db.commit()
    with patch.object(DataFiles, "delete") as mock_delete:
        manager.migrate()
        mock_delete.assert_not_called()
    assert manager._get_version() == 34


def test_migrate_latest(db):
    """Test migration at the latest version (no migration needed)."""
    manager = DatabaseManager(session=db)
    cursor = db.connection().connection.cursor()
    cursor.execute("pragma user_version = 34")
    db.commit()
    manager.migrate()
    version = manager._get_version()
    assert version == 34


def test_get_version(db):
    """Test _get_version returns the current pragma version."""
    manager = DatabaseManager(session=db)
    version = manager._get_version()
    assert isinstance(version, int)
