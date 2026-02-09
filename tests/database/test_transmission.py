from app.database.transmission import Transmission
from app.database.database_tables import (
    TransmissionTable,
    User as UserDB,
)
from sqlalchemy.orm import Session


def _clean(db: Session):
    db.query(TransmissionTable).delete()
    db.query(UserDB).delete()
    db.commit()


def _setup_user(db: Session):
    user = UserDB(identifier="user_tx", email="tx@example.com", display_name="TX User")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_transmission(
    db: Session, user, version=1, study="Study A", status="pending"
):
    return Transmission.create(
        version=version,
        study=study,
        status=status,
        user_id=user.id,
        session=db,
    )


def test_create(db):
    _clean(db)
    user = _setup_user(db)
    tx = _create_transmission(db, user)
    assert tx is not None
    assert tx.version == 1
    assert tx.study == "Study A"
    assert tx.status == "pending"
    assert tx.user_id == user.id


def test_find_exists(db):
    _clean(db)
    user = _setup_user(db)
    tx = _create_transmission(db, user)
    found = Transmission.find(tx.id, db)
    assert found is not None
    assert found.id == tx.id


def test_find_not_exists(db):
    _clean(db)
    assert Transmission.find(99999, db) is None


def test_page_first(db):
    _clean(db)
    user = _setup_user(db)
    for i in range(15):
        _create_transmission(db, user, version=i, study=f"Study {i}")
    result = Transmission.page(1, 10, user.id, db)
    assert result["count"] == 15
    assert len(result["items"]) == 10


def test_page_empty(db):
    _clean(db)
    user = _setup_user(db)
    result = Transmission.page(1, 10, user.id, db)
    assert result["count"] == 0
    assert len(result["items"]) == 0


def test_page_zero_values(db):
    _clean(db)
    user = _setup_user(db)
    _create_transmission(db, user)
    result = Transmission.page(0, 0, user.id, db)
    assert result["page"] == 1
    assert result["size"] == 10


def test_debug(db):
    _clean(db)
    user = _setup_user(db)
    _create_transmission(db, user, status="done")
    result = Transmission.debug(db)
    assert result["count"] == 1
    assert len(result["items"]) == 1
    assert "_sa_instance_state" not in result["items"][0]


def test_update_status(db):
    _clean(db)
    user = _setup_user(db)
    tx = _create_transmission(db, user, status="pending")
    updated = tx.update_status("completed", db)
    assert updated.status == "completed"
