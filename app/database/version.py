from pydantic import BaseModel, ConfigDict
from app.database.database_tables import Version as VersionDB
from sqlalchemy.orm import Session
from sqlalchemy import desc


class VersionBase(BaseModel):
    version: int


class VersionCreate(VersionBase):
    pass


class Version(VersionBase):
    id: int
    study_id: int
    import_id: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(cls, version: int, study_id: int, session: Session) -> "Version":
        db_item = VersionDB(version=version)
        session.add(**db_item, study_id=study_id)
        session.commit()
        session.refresh(db_item)
        return cls(**db_item.__dict__)

    @classmethod
    def find(cls, id: int, session: Session) -> "Version":
        db_item = session.query(VersionDB).filter(VersionDB.id == id).first()
        return cls(**db_item.__dict__) if db_item else None

    @classmethod
    def find_by_name(cls, name: str, session: Session) -> "Version":
        db_item = session.query(VersionDB).filter(VersionDB.name == name).first()
        return cls(**db_item.__dict__) if db_item else None

    @classmethod
    def find_latest_version(cls, study_id, session: Session) -> "Version":
        db_item = (
            session.query(VersionDB)
            .filter(VersionDB.study_id == study_id)
            .order_by(desc(VersionDB.version))
            .first()
        )
        return db_item if db_item else None

    @classmethod
    def version_count(cls, study_id, session: Session) -> int:
        return session.query(VersionDB).filter(VersionDB.study_id == study_id).count()

    @classmethod
    def page(
        cls, page: int, size: int, filter: str, study_id: int, session: Session
    ) -> list[dict]:
        page = page if page >= 1 else 1
        size = size if size > 0 else 10
        skip = (page - 1) * size
        count = session.query(VersionDB).filter(VersionDB.study_id == study_id).count()
        data = (
            session.query(VersionDB)
            .filter(VersionDB.study_id == study_id)
            .offset(skip)
            .limit(size)
            .all()
        )
        results = []
        for db_item in data:
            results.append(db_item.__dict__)
            results[-1].pop("_sa_instance_state")
        result = {
            "items": results,
            "page": page,
            "size": size,
            "filter": "",
            "count": count,
        }
        return result

    @classmethod
    def debug(cls, session: Session) -> list[dict]:
        count = session.query(VersionDB).count()
        data = session.query(VersionDB).all()
        results = []
        for db_item in data:
            results.append(db_item.__dict__)
            results[-1].pop("_sa_instance_state")
        result = {"items": results, "count": count}
        return result
