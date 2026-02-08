from unittest.mock import patch
from app.database.database_manager import DatabaseManager
from app.database.database_tables import (
    Study as StudyDB,
    Version as VersionDB,
    FileImport as FileImportDB,
    Endpoint as EndpointDB,
    UserEndpoint as UserEndpointDB,
    User as UserDB,
    TransmissionTable as TransmissionDB,
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
    assert db.query(UserDB).count() > 0
    assert db.query(StudyDB).count() > 0

    # Execute clear_all with a mock for DataFiles().delete_all()
    with patch.object(DataFiles, "delete_all") as mock_delete_all:
        manager = DatabaseManager()
        manager.clear_all()

        # Verify all tables were cleared
        assert db.query(StudyDB).count() == 0
        assert db.query(VersionDB).count() == 0
        assert db.query(FileImportDB).count() == 0
        assert db.query(EndpointDB).count() == 0
        assert db.query(UserEndpointDB).count() == 0
        assert db.query(TransmissionDB).count() == 0

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
    # Verify version was updated to 31
    version = manager._get_version()
    assert version == 31


def test_migrate_at_31(db):
    """Test migration when version == 31."""
    manager = DatabaseManager(session=db)
    cursor = db.connection().connection.cursor()
    cursor.execute("pragma user_version = 31")
    db.commit()
    manager.migrate()
    version = manager._get_version()
    assert version == 32


def test_migrate_above_31(db):
    """Test migration when version > 31 (no migration needed)."""
    manager = DatabaseManager(session=db)
    cursor = db.connection().connection.cursor()
    cursor.execute("pragma user_version = 32")
    db.commit()
    manager.migrate()
    version = manager._get_version()
    assert version == 32


def test_get_version(db):
    """Test _get_version returns the current pragma version."""
    manager = DatabaseManager(session=db)
    version = manager._get_version()
    assert isinstance(version, int)
