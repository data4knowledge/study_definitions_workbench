import pytest
from app.database.user import User
from app.database.endpoint import Endpoint
from app.model.exceptions import FindException
from app.database.database_tables import (
    User as UserDB,
    Endpoint as EndpointDB,
    UserEndpoint as UserEndpointDB,
)
from sqlalchemy.orm import Session


def _clean(db: Session):
    db.query(UserEndpointDB).delete()
    db.query(EndpointDB).delete()
    db.query(UserDB).delete()
    db.commit()


def test_single_user(db):
    results = User.single_user()
    assert results == {
        "email": "",
        "sub": "SUE|1234567890",
        "nickname": "Single User",
        "roles": [],
    }


def test_create_valid(db):
    _clean(db)
    user, validation = User.create("ident_1", "valid@example.com", "Valid Name", db)
    assert user is not None
    assert user.identifier == "ident_1"
    assert user.email == "valid@example.com"
    assert validation["display_name"]["valid"] is True


def test_create_invalid_display_name(db):
    _clean(db)
    user, validation = User.create("ident_2", "bad@example.com", "Bad!@#Name", db)
    assert user is None
    assert validation["display_name"]["valid"] is False


def test_find_exists(db):
    _clean(db)
    user, _ = User.create("ident_find", "find@example.com", "Find Me", db)
    found = User.find(user.id, db)
    assert found is not None
    assert found.identifier == "ident_find"


def test_find_not_exists(db):
    _clean(db)
    with pytest.raises(FindException):
        User.find(99999, db)


def test_find_by_email(db):
    _clean(db)
    User.create("ident_email", "email@example.com", "Email User", db)
    found = User.find_by_email("email@example.com", db)
    assert found is not None
    assert found.email == "email@example.com"


def test_find_by_email_not_found(db):
    _clean(db)
    assert User.find_by_email("nonexistent@example.com", db) is None


def test_find_by_identifier(db):
    _clean(db)
    User.create("ident_abc", "abc@example.com", "ABC User", db)
    found = User.find_by_identifier("ident_abc", db)
    assert found is not None
    assert found.identifier == "ident_abc"


def test_check_existing_user(db):
    _clean(db)
    User.create("sub_existing", "exist@example.com", "Existing", db)
    info = {"sub": "sub_existing", "email": "exist@example.com", "nickname": "Existing"}
    user, present = User.check(info, db)
    assert user is not None
    assert present is True


def test_check_new_user(db):
    _clean(db)
    info = {"sub": "sub_new", "email": "new@example.com", "nickname": "NewUser"}
    user, present = User.check(info, db)
    assert user is not None
    assert present is False
    assert user.identifier == "sub_new"


def test_check_no_email(db):
    _clean(db)
    info = {"sub": "sub_noemail", "nickname": "NoEmail"}
    user, present = User.check(info, db)
    assert user is not None
    assert user.email == "No email"


def test_update_display_name_valid(db):
    _clean(db)
    user, _ = User.create("ident_upd", "upd@example.com", "Original", db)
    updated, validation = user.update_display_name("Updated Name", db)
    assert updated is not None
    assert updated.display_name == "Updated Name"
    assert validation["display_name"]["valid"] is True


def test_update_display_name_invalid(db):
    _clean(db)
    user, _ = User.create("ident_upd2", "upd2@example.com", "Original", db)
    updated, validation = user.update_display_name("Bad!@#", db)
    assert updated is None
    assert validation["display_name"]["valid"] is False


def test_endpoints_page(db):
    _clean(db)
    user, _ = User.create("ident_ep", "ep@example.com", "EP User", db)
    Endpoint.create(
        name="EP1",
        endpoint="https://ep1.test/api",
        type="FHIR",
        user_id=user.id,
        session=db,
    )
    Endpoint.create(
        name="EP2",
        endpoint="https://ep2.test/api",
        type="FHIR",
        user_id=user.id,
        session=db,
    )
    result = User.endpoints_page(1, 10, user.id, db)
    assert result["count"] == 2
    assert len(result["items"]) == 2


def test_debug(db):
    _clean(db)
    User.create("ident_dbg", "dbg@example.com", "Debug User", db)
    result = User.debug(db)
    assert result["count"] == 1
    assert len(result["items"]) == 1
    assert "_sa_instance_state" not in result["items"][0]


def test_is_valid_true():
    valid, validation = User._is_valid("ident", "e@e.com", "Valid Name")
    assert valid is True


def test_is_valid_false():
    valid, validation = User._is_valid("ident", "e@e.com", "Bad!@#")
    assert valid is False


def test_valid():
    v = User.valid()
    assert v["display_name"]["valid"] is True
    assert v["email"]["valid"] is True
    assert v["identifier"]["valid"] is True
