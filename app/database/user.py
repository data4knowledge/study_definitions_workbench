import re
from typing import ClassVar
from pydantic import BaseModel, ConfigDict
from app.database.database_tables import User as UserDB
from app.model.exceptions import FindException
from sqlalchemy.orm import Session
from d4k_ms_base.logger import application_logger


class UserBase(BaseModel):
    identifier: str
    email: str
    display_name: str
    is_active: bool
    roles: str = ""


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls,
        identifier: str,
        email: str,
        display_name: str,
        session: Session,
        roles: str = "",
    ) -> "User":
        valid, validation = cls._is_valid(
            identifier=identifier, email=email, display_name=display_name
        )
        if valid:
            db_item = UserDB(
                identifier=identifier,
                email=email,
                display_name=display_name,
                roles=roles,
            )
            session.add(db_item)
            session.commit()
            session.refresh(db_item)
            return cls(**db_item.__dict__), validation
        else:
            return None, validation

    @classmethod
    def find(cls, id: int, session: Session) -> "User":
        db_item = session.query(UserDB).filter(UserDB.id == id).first()
        if db_item:
            return cls(**db_item.__dict__)
        else:
            application_logger.error(f"Failed to find User with id '{id}'")
            raise FindException(cls, id)

    @classmethod
    def find_by_email(cls, email: str, session: Session):
        db_item = session.query(UserDB).filter(UserDB.email == email).first()
        return cls(**db_item.__dict__) if db_item else None

    @classmethod
    def find_by_identifier(cls, identifier: str, session: Session):
        db_item = session.query(UserDB).filter(UserDB.identifier == identifier).first()
        return cls(**db_item.__dict__) if db_item else None

    @classmethod
    def endpoints_page(
        cls, page: int, size: int, user_id: int, session: Session
    ) -> list[dict]:
        page = page if page >= 1 else 1
        size = size if size > 0 else 10
        skip = (page - 1) * size
        user = session.query(UserDB).filter(UserDB.id == user_id).first()
        count = len(user.endpoints)
        data = user.endpoints[skip : skip + size]
        results = []
        for db_item in data:
            results.append(db_item.__dict__)
        result = {
            "items": results,
            "page": page,
            "size": size,
            "filter": "",
            "count": count,
        }
        return result

    @classmethod
    def check(cls, info: dict, session: Session):
        present_in_db = True
        # validation = cls.valid()
        user = cls.find_by_identifier(info["sub"], session)
        if not user:
            # print(f"USER: Not in DB")
            present_in_db = False
            dn = re.sub(r"[^a-zA-Z0-9]", "", info["nickname"])
            email = info["email"] if "email" in info else "No email"
            display_name = dn if dn else "No display name"
            user, validation = cls.create(info["sub"], email, display_name, session)
        return user, present_in_db

    @classmethod
    def debug(cls, session: Session) -> list[dict]:
        count = session.query(UserDB).count()
        data = session.query(UserDB).all()
        results = []
        for db_item in data:
            results.append(db_item.__dict__)
            results[-1].pop("_sa_instance_state")
        result = {"items": results, "count": count}
        return result

    @classmethod
    def single_user(cls) -> list[dict]:
        return {
            "email": "",
            "sub": "SUE|1234567890",
            "nickname": "Single User",
            "roles": [{"name": "Admin"}, {"name": "Transmit"}],
        }

    # Users at this domain always get full rights (see effective_role_names).
    ADMIN_DOMAIN: ClassVar[str] = "data4knowledge.dk"
    # Roles an admin can grant via the management screen.
    ALL_ROLES: ClassVar[list[str]] = ["Admin", "Transmit"]

    @classmethod
    def is_admin_domain(cls, email: str) -> bool:
        return (email or "").strip().lower().endswith(f"@{cls.ADMIN_DOMAIN}")

    @classmethod
    def domain_roles(cls, email: str) -> str:
        """Roles automatically granted by email domain (comma-separated)."""
        return "Admin,Transmit" if cls.is_admin_domain(email) else ""

    def stored_role_names(self) -> list[str]:
        return [r.strip() for r in self.roles.split(",") if r.strip()]

    def effective_role_names(self) -> list[str]:
        """Stored roles plus any granted automatically by email domain."""
        names = list(self.stored_role_names())
        for r in self.domain_roles(self.email).split(","):
            r = r.strip()
            if r and r not in names:
                names.append(r)
        return names

    def roles_list(self) -> list[dict]:
        """Effective roles in the shape the app expects: ``[{"name": ...}]``."""
        return [{"name": r} for r in self.effective_role_names()]

    def has_role(self, role: str) -> bool:
        return role in self.effective_role_names()

    def session_info(self) -> dict:
        """Build the ``userinfo`` dict stored in ``request.session``.

        Mirrors the structure Auth0 previously placed in the session so
        that every downstream consumer (``user_details``,
        ``admin_role_enabled`` etc.) works unchanged.
        """
        return {
            "email": self.email,
            "sub": self.identifier,
            "nickname": self.display_name,
            "roles": self.roles_list(),
        }

    @classmethod
    def list_all(cls, session: Session) -> list["User"]:
        return [cls(**item.__dict__) for item in session.query(UserDB).all()]

    @classmethod
    def register(cls, email: str, display_name: str, session: Session):
        """Self-registration: create a user, applying domain-based roles.

        Returns ``(user, validation, already_existed)``.
        """
        email = (email or "").strip().lower()
        existing = cls.find_by_email(email, session)
        if existing:
            return existing, cls.valid(), True
        user, validation = cls.create(
            email, email, display_name, session, roles=cls.domain_roles(email)
        )
        return user, validation, False

    def set_roles(self, roles: list[str], session: Session) -> "User":
        """Replace this user's stored roles (admin management screen)."""
        clean = ",".join([r for r in roles if r in self.__class__.ALL_ROLES])
        db_item = session.query(UserDB).filter(UserDB.id == self.id).first()
        db_item.roles = clean
        session.commit()
        session.refresh(db_item)
        return self.__class__(**db_item.__dict__)

    def update_display_name(self, display_name: str, session: Session) -> "User":
        db_item = session.query(UserDB).filter(UserDB.id == self.id).first()
        valid, validation = self.__class__._is_valid(
            db_item.identifier, db_item.email, display_name
        )
        if valid:
            db_item.display_name = display_name
            session.commit()
            session.refresh(db_item)
            return self.__class__(**db_item.__dict__), validation
        else:
            return None, validation

    @classmethod
    def valid(cls):
        return {
            "display_name": {"valid": True, "message": ""},
            "email": {"valid": True, "message": ""},
            "identifier": {"valid": True, "message": ""},
        }

    @staticmethod
    def _is_valid(
        identifier: str, email: str, display_name: str
    ) -> tuple["UserDB", dict]:
        dn_validation = bool(re.match("[a-zA-Z0-9 ]+$", display_name))
        validation = {
            "display_name": {
                "valid": dn_validation,
                "message": "A display name should only contain alphanumeric characters or spaces"
                if not dn_validation
                else None,
            },
            "email": {"valid": True, "message": ""},
            "identifier": {"valid": True, "message": ""},
        }
        valid = all(value["valid"] for value in validation.values())
        return valid, validation
