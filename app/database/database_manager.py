import os
from app.database import database_tables
from app.database.database import engine, SessionLocal
from app.database.database_tables import (
    Study as StudyDB,
    Version as VersionDB,
    FileImport as FileImportDB,
    Endpoint as EndpointDB,
)
from app.database.database_tables import (
    UserEndpoint as UserEndpointDB,
    User as UserDB,
    TransmissionTable as TransmissionDB,
)
from app.model.file_handling.data_files import DataFiles
from sqlalchemy.orm import Session
from d4kms_generic import application_logger
from app.configuration.configuration import application_configuration


class DatabaseManager:
    def __init__(self, session: Session = None):
        self.session: Session = session if session else SessionLocal()

    def check(self):
        dir = application_configuration.database_path
        application_logger.info("Checking database dir exists")
        try:
            os.mkdir(dir)
            application_logger.info("Database dir created")
            database_tables.Base.metadata.create_all(bind=engine)
            application_logger.info("Database created")
            return True
        except FileExistsError:
            application_logger.info("Database dir exists")
            database_tables.Base.metadata.create_all(bind=engine)
            return False
        except Exception as e:
            application_logger.exception(
                f"Exception checking/creating database dir '{dir}'", e
            )
            return False

    def clear_all(self):
        self.session.query(StudyDB).delete()
        self.session.query(VersionDB).delete()
        self.session.query(FileImportDB).delete()
        self.session.query(EndpointDB).delete()
        self.session.query(UserEndpointDB).delete()
        self.session.query(TransmissionDB).delete()
        self.session.commit()
        DataFiles().delete_all()

    def clear_users(self):
        self.session.query(UserDB).delete()
        self.session.commit()

    def migrate(self):
        version = self._get_version()
        print(f"VERSION: {version}")
        if version != 31:  # Do it anyway
            cursor = self.session.connection().connection.cursor()
            new_types = (
                {"old": "", "new": "1111"},
                {"old": "XLSX", "new": "USDM_EXCEL"},
                {"old": "FHIR_V1", "new": "FHIR_V1_JSON"},
                {"old": "DOCX", "new": "M11_DOCX"},
            )
            cursor.executemany("UPDATE import SET type=:new WHERE type=:old", new_types)
            cursor.execute("pragma user_version = 31")
            self.session.commit()

    def _get_version(self):
        cursor = self.session.connection().connection.cursor()
        cursor.execute("pragma user_version")
        return cursor.fetchone()[0]
