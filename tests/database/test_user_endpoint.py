from app.database.user_endpoint import UserEndpoint
from app.database.database_tables import (
    UserEndpoint as UserEndpointDB,
    User as UserDB,
    Endpoint as EndpointDB,
)
from sqlalchemy.orm import Session


def _clean(db: Session):
    db.query(UserEndpointDB).delete()
    db.query(EndpointDB).delete()
    db.query(UserDB).delete()
    db.commit()


def test_debug_empty(db):
    _clean(db)
    result = UserEndpoint.debug(db)
    assert result["count"] == 0
    assert len(result["items"]) == 0


def test_debug_with_data(db):
    _clean(db)
    user = UserDB(identifier="user_ue", email="ue@example.com", display_name="UE User")
    db.add(user)
    db.commit()
    db.refresh(user)

    endpoint = EndpointDB(type="FHIR", name="Test EP", endpoint="https://ep.test/api")
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)

    ue = UserEndpointDB(user_id=user.id, endpoint_id=endpoint.id)
    db.add(ue)
    db.commit()

    result = UserEndpoint.debug(db)
    assert result["count"] == 1
    assert len(result["items"]) == 1
    assert "_sa_instance_state" not in result["items"][0]
    assert result["items"][0]["user_id"] == user.id
    assert result["items"][0]["endpoint_id"] == endpoint.id
