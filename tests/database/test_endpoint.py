from unittest.mock import patch, MagicMock
from app.database.endpoint import Endpoint
from app.database.database_tables import (
    Endpoint as EndpointDB,
    User as UserDB,
    UserEndpoint as UserEndpointDB,
)


def _clean_db(db):
    """Clean the database before tests."""
    db.query(UserDB).delete()
    db.query(EndpointDB).delete()
    db.query(UserEndpointDB).delete()
    db.commit()


def test_create_new_endpoint(db):
    """Test creating a new endpoint."""
    # Clean the database first
    _clean_db(db)

    # Create a test user
    user = UserDB(
        identifier="user_endpoint_create",
        email="test_endpoint_create@example.com",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a new endpoint
    endpoint, validation = Endpoint.create(
        name="Test Endpoint",
        endpoint="https://example.com/api",
        type="FHIR",
        user_id=user.id,
        session=db,
    )

    # Verify endpoint was created
    assert endpoint is not None
    assert endpoint.name == "Test Endpoint"
    assert endpoint.endpoint == "https://example.com/api"
    assert endpoint.type == "FHIR"
    assert validation["name"]["valid"] is True
    assert validation["endpoint"]["valid"] is True
    assert validation["type"]["valid"] is True

    # Verify endpoint was associated with user
    db_user = db.query(UserDB).filter(UserDB.id == user.id).first()
    assert len(db_user.endpoints) == 1
    assert db_user.endpoints[0].name == "Test Endpoint"


def test_create_existing_endpoint(db):
    """Test creating an endpoint that already exists."""
    # Clean the database first
    _clean_db(db)

    # Create a test user
    user1 = UserDB(
        identifier="user_endpoint_create1",
        email="test_endpoint_create1@example.com",
        display_name="Test User 1",
    )
    db.add(user1)
    db.commit()
    db.refresh(user1)

    # Create a new endpoint for user1
    endpoint1, validation1 = Endpoint.create(
        name="Test Endpoint",
        endpoint="https://example.com/api",
        type="FHIR",
        user_id=user1.id,
        session=db,
    )

    # Create another user
    user2 = UserDB(
        identifier="user_endpoint_create2",
        email="test_endpoint_create2@example.com",
        display_name="Test User 2",
    )
    db.add(user2)
    db.commit()
    db.refresh(user2)

    # Create the same endpoint for user2
    endpoint2, validation2 = Endpoint.create(
        name="Test Endpoint",
        endpoint="https://example.com/api",
        type="FHIR",
        user_id=user2.id,
        session=db,
    )

    # Verify both users have the same endpoint
    db_user1 = db.query(UserDB).filter(UserDB.id == user1.id).first()
    db_user2 = db.query(UserDB).filter(UserDB.id == user2.id).first()
    assert len(db_user1.endpoints) == 1
    assert len(db_user2.endpoints) == 1
    assert db_user1.endpoints[0].id == db_user2.endpoints[0].id


def test_create_invalid_endpoint(db):
    """Test creating an endpoint with invalid data."""
    # Clean the database first
    _clean_db(db)

    # Create a test user
    user = UserDB(
        identifier="user_endpoint_invalid",
        email="test_endpoint_invalid@example.com",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create an endpoint with invalid name
    endpoint1, validation1 = Endpoint.create(
        name="Test Endpoint!@#",  # Invalid name with special characters
        endpoint="https://example.com/api",
        type="FHIR",
        user_id=user.id,
        session=db,
    )

    # Verify endpoint was not created
    assert endpoint1 is None
    assert validation1["name"]["valid"] is False
    assert "alphanumeric" in validation1["name"]["message"]

    # Create an endpoint with invalid URL
    endpoint2, validation2 = Endpoint.create(
        name="Test Endpoint",
        endpoint="not-a-url",  # Invalid URL
        type="FHIR",
        user_id=user.id,
        session=db,
    )

    # Verify endpoint was not created
    assert endpoint2 is None
    assert validation2["endpoint"]["valid"] is False
    assert "valid URL" in validation2["endpoint"]["message"]

    # Create an endpoint with invalid type
    endpoint3, validation3 = Endpoint.create(
        name="Test Endpoint",
        endpoint="https://example.com/api",
        type="INVALID",  # Invalid type
        user_id=user.id,
        session=db,
    )

    # Verify endpoint was not created
    assert endpoint3 is None
    assert validation3["type"]["valid"] is False
    assert "FHIR" in validation3["type"]["message"]


def test_find_by_endpoint(db):
    """Test finding an endpoint by its URL."""
    # Clean the database first
    _clean_db(db)

    # Create a test user
    user = UserDB(
        identifier="user_find_endpoint",
        email="test_find_endpoint@example.com",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a new endpoint
    endpoint_url = "https://example.com/api"
    endpoint, _ = Endpoint.create(
        name="Test Endpoint",
        endpoint=endpoint_url,
        type="FHIR",
        user_id=user.id,
        session=db,
    )

    # Find the endpoint by URL
    found_endpoint = Endpoint.find_by_endpoint(endpoint_url, db)

    # Verify endpoint was found
    assert found_endpoint is not None
    assert found_endpoint.name == "Test Endpoint"
    assert found_endpoint.endpoint == endpoint_url
    assert found_endpoint.type == "FHIR"

    # Try to find a non-existent endpoint
    not_found_endpoint = Endpoint.find_by_endpoint("https://nonexistent.com/api", db)

    # Verify endpoint was not found
    assert not_found_endpoint is None


def test_find(db):
    """Test finding an endpoint by its ID."""
    # Clean the database first
    _clean_db(db)

    # Create a test user
    user = UserDB(
        identifier="user_find_id",
        email="test_find_id@example.com",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a new endpoint
    endpoint, _ = Endpoint.create(
        name="Test Endpoint",
        endpoint="https://example.com/api",
        type="FHIR",
        user_id=user.id,
        session=db,
    )

    # Find the endpoint by ID
    found_endpoint = Endpoint.find(endpoint.id, db)

    # Verify endpoint was found
    assert found_endpoint is not None
    assert found_endpoint.name == "Test Endpoint"
    assert found_endpoint.endpoint == "https://example.com/api"
    assert found_endpoint.type == "FHIR"

    # Try to find a non-existent endpoint
    not_found_endpoint = Endpoint.find(9999, db)

    # Verify endpoint was not found
    assert not_found_endpoint is None


def test_debug(db):
    """Test the debug method."""
    # Clean the database first
    _clean_db(db)

    # Create a test user
    user = UserDB(
        identifier="user_debug",
        email="test_debug@example.com",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create some endpoints
    Endpoint.create(
        name="Test Endpoint 1",
        endpoint="https://example1.com/api",
        type="FHIR",
        user_id=user.id,
        session=db,
    )

    Endpoint.create(
        name="Test Endpoint 2",
        endpoint="https://example2.com/api",
        type="FHIR",
        user_id=user.id,
        session=db,
    )

    # Get debug info
    debug_info = Endpoint.debug(db)

    # Verify debug info
    assert debug_info["count"] == 2
    assert len(debug_info["items"]) == 2
    assert debug_info["items"][0]["name"] == "Test Endpoint 1"
    assert debug_info["items"][1]["name"] == "Test Endpoint 2"
    assert "_sa_instance_state" not in debug_info["items"][0]
    assert "_sa_instance_state" not in debug_info["items"][1]


def test_delete_endpoint_with_multiple_users(db):
    """Test deleting an endpoint that is associated with multiple users."""
    # Clean the database first
    _clean_db(db)

    # Create test users
    user1 = UserDB(
        identifier="user_delete1",
        email="test_delete1@example.com",
        display_name="Test User 1",
    )
    db.add(user1)
    db.commit()
    db.refresh(user1)

    user2 = UserDB(
        identifier="user_delete2",
        email="test_delete2@example.com",
        display_name="Test User 2",
    )
    db.add(user2)
    db.commit()
    db.refresh(user2)

    # Create an endpoint and associate it with both users
    endpoint_url = "https://example.com/api"
    endpoint1, _ = Endpoint.create(
        name="Test Endpoint",
        endpoint=endpoint_url,
        type="FHIR",
        user_id=user1.id,
        session=db,
    )

    endpoint2, _ = Endpoint.create(
        name="Test Endpoint",
        endpoint=endpoint_url,
        type="FHIR",
        user_id=user2.id,
        session=db,
    )

    # Delete the endpoint for user1
    endpoint1.delete(user1.id, db)

    # Verify the endpoint is still in the database (because user2 still has it)
    db_endpoint = (
        db.query(EndpointDB).filter(EndpointDB.endpoint == endpoint_url).first()
    )
    assert db_endpoint is not None

    # Verify user1 no longer has the endpoint
    db_user1 = db.query(UserDB).filter(UserDB.id == user1.id).first()
    assert len(db_user1.endpoints) == 0

    # Verify user2 still has the endpoint
    db_user2 = db.query(UserDB).filter(UserDB.id == user2.id).first()
    assert len(db_user2.endpoints) == 1


def test_delete_endpoint_with_single_user(db):
    """Test deleting an endpoint that is associated with a single user."""
    # Clean the database first
    _clean_db(db)

    # Create a test user
    user = UserDB(
        identifier="user_delete_single",
        email="test_delete_single@example.com",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create an endpoint
    endpoint_url = "https://example.com/api"
    endpoint, _ = Endpoint.create(
        name="Test Endpoint",
        endpoint=endpoint_url,
        type="FHIR",
        user_id=user.id,
        session=db,
    )

    # Get the endpoint from the database
    db_endpoint = (
        db.query(EndpointDB).filter(EndpointDB.endpoint == endpoint_url).first()
    )
    assert db_endpoint is not None

    # Delete the endpoint
    result = endpoint.delete(user.id, db)

    # Verify the delete method returned success
    assert result == 1

    # Verify user no longer has the endpoint
    db_user = db.query(UserDB).filter(UserDB.id == user.id).first()
    assert len(db_user.endpoints) == 0

    # Verify the user_endpoint association is removed
    user_endpoint = (
        db.query(UserEndpointDB).filter(UserEndpointDB.endpoint_id == endpoint.id).all()
    )
    assert len(user_endpoint) == 0


def test_delete_endpoint_with_no_users():
    """Test deleting an endpoint that has no users associated with it."""
    # Create a mock endpoint object with a delete method
    mock_endpoint = MagicMock()

    # Create a mock session
    mock_session = MagicMock()

    # Set up the mock query results
    mock_session.query.side_effect = lambda model: {
        EndpointDB: MagicMock(
            filter=lambda *args: MagicMock(first=lambda: mock_endpoint)
        ),
        UserDB: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: MagicMock(endpoints=MagicMock(remove=MagicMock()))
            )
        ),
        UserEndpointDB: MagicMock(filter=lambda *args: MagicMock(all=lambda: [])),
    }[model]

    # Create an endpoint instance
    endpoint = Endpoint(
        id=1, name="Test Endpoint", endpoint="https://example.com/api", type="FHIR"
    )

    # Patch the delete method on the mock_endpoint
    with patch.object(mock_endpoint, "delete") as mock_delete:
        # Delete the endpoint
        result = endpoint.delete(user_id=1, session=mock_session)

        # Verify the delete method was called
        mock_delete.assert_called_once()

    # Verify the delete method returned success
    assert result == 1


def test_valid():
    """Test the valid method."""
    # Call the valid method
    validation = Endpoint.valid()

    # Verify validation results
    assert validation["name"]["valid"] is True
    assert validation["endpoint"]["valid"] is True
    assert validation["type"]["valid"] is True
    assert validation["name"]["message"] == ""
    assert validation["endpoint"]["message"] == ""
    assert validation["type"]["message"] == ""


def test_is_valid():
    """Test the _is_valid method."""
    # Test with valid data
    valid, validation = Endpoint._is_valid(
        name="Test Endpoint", endpoint="https://example.com/api", type="FHIR"
    )

    # Verify validation results
    assert valid is True
    assert validation["name"]["valid"] is True
    assert validation["endpoint"]["valid"] is True
    assert validation["type"]["valid"] is True

    # Test with invalid name
    valid, validation = Endpoint._is_valid(
        name="Test Endpoint!@#",  # Invalid name with special characters
        endpoint="https://example.com/api",
        type="FHIR",
    )

    # Verify validation results
    assert valid is False
    assert validation["name"]["valid"] is False
    assert "alphanumeric" in validation["name"]["message"]

    # Test with invalid URL
    valid, validation = Endpoint._is_valid(
        name="Test Endpoint",
        endpoint="not-a-url",  # Invalid URL
        type="FHIR",
    )

    # Verify validation results
    assert valid is False
    assert validation["endpoint"]["valid"] is False
    assert "valid URL" in validation["endpoint"]["message"]

    # Test with invalid type
    valid, validation = Endpoint._is_valid(
        name="Test Endpoint",
        endpoint="https://example.com/api",
        type="INVALID",  # Invalid type
    )

    # Verify validation results
    assert valid is False
    assert validation["type"]["valid"] is False
    assert "FHIR" in validation["type"]["message"]
