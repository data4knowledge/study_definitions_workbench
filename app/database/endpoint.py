import re
from typing import Optional
from pydantic import BaseModel, HttpUrl, TypeAdapter, ConfigDict
from sqlalchemy.orm import Session
from app.database.database_tables import Endpoint as EndpointDB
from app.database.database_tables import UserEndpoint as UserEndpointDB
from app.database.database_tables import User as UserDB

http_url_adapter = TypeAdapter(HttpUrl)


class EndpointBase(BaseModel):
    name: str
    endpoint: str
    type: str


class Endpoint(EndpointBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls, name: str, endpoint: str, type: str, user_id: int, session: Session
    ) -> "Endpoint":
        db_item = (
            session.query(EndpointDB).filter(EndpointDB.endpoint == endpoint).first()
        )
        user = session.query(UserDB).filter(UserDB.id == user_id).first()
        if not db_item:
            valid, validation = cls._is_valid(name, endpoint, type)
            if not valid:
                return None, validation
            data = {"name": name, "endpoint": endpoint, "type": type}
            db_item = EndpointDB(**data)
            session.add(db_item)
        user.endpoints.append(db_item)
        session.add(user)
        session.commit()
        session.refresh(db_item)
        return cls(**db_item.__dict__), cls.valid()

    @classmethod
    def find_by_endpoint(cls, endpoint: str, session: Session):
        db_item = (
            session.query(EndpointDB).filter(EndpointDB.endpoint == endpoint).first()
        )
        return cls(**db_item.__dict__) if db_item else None

    @classmethod
    def find(cls, id: int, session: Session) -> Optional["Endpoint"]:
        db_item = session.query(EndpointDB).filter(EndpointDB.id == id).first()
        return cls(**db_item.__dict__) if db_item else None

    @classmethod
    def debug(cls, session: Session) -> list[dict]:
        count = session.query(EndpointDB).count()
        data = session.query(EndpointDB).all()
        results = []
        for db_item in data:
            results.append(db_item.__dict__)
            results[-1].pop("_sa_instance_state")
        result = {"items": results, "count": count}
        return result

    def delete(self, user_id: int, session: Session) -> int:
        endpoint = session.query(EndpointDB).filter(EndpointDB.id == self.id).first()
        user = session.query(UserDB).filter(UserDB.id == user_id).first()
        user.endpoints.remove(endpoint)
        user_endpoint = (
            session.query(UserEndpointDB)
            .filter(UserEndpointDB.endpoint_id == endpoint.id)
            .all()
        )
        if len(user_endpoint) == 0:
            endpoint.delete()
        session.commit()
        return 1

    @classmethod
    def valid(cls):
        result = {}
        for attribute, definition in EndpointBase.model_fields.items():
            result[attribute] = {"valid": True, "message": ""}
        # print(f"ENDPOINT VALID: {result}")
        return result

    @staticmethod
    def _is_valid(name: str, endpoint: str, type: str) -> tuple[bool, dict]:
        name_validation = bool(re.match("[a-zA-Z0-9 ]+$", name))
        try:
            http_url_adapter.validate_python(endpoint)
            endpoint_valiadation = True
        except Exception as e:
            endpoint_valiadation = False
        type_valiadation = type in ["FHIR"]
        validation = {
            "name": {
                "valid": name_validation,
                "message": "An endpoint name should only contain alphanumeric characters or spaces"
                if not name_validation
                else "",
            },
            "endpoint": {
                "valid": endpoint_valiadation,
                "message": "An endpoint should be a valid URL"
                if not endpoint_valiadation
                else "",
            },
            "type": {
                "valid": type_valiadation,
                "message": "Type should be 'FHIR'" if not type_valiadation else "",
            },
        }
        valid = all(value["valid"] == True for value in validation.values())
        # print(f"ENDPOINT VALIDATION: {validation}")
        return valid, validation
