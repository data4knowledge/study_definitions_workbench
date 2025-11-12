import datetime
from app.database.user import User
from app.database.file_import import FileImport
from app.database.endpoint import Endpoint
from app.database.study import Study
from app.database.version import Version
# from tests.mocks.fastapi_mocks import protect_endpoint, mock_authorisation, mock_client, mock_client_multiple, mock_async_client


def factory_user() -> User:
    return User(
        **{
            "identifier": "FRED",
            "email": "fred@example.com",
            "display_name": "Fred Smith",
            "is_active": True,
            "id": 1,
        }
    )


def factory_user_2() -> User:
    return User(
        **{
            "identifier": "FRED",
            "email": "fred@example.com",
            "display_name": "Fred Smithy",
            "is_active": True,
            "id": 1,
        }
    )


def factory_study() -> Study:
    return Study(
        **{
            "name": "STUDYNAME",
            "title": "Study Title",
            "phase": "Phase 1",
            "sponsor": "ACME",
            "sponsor_identifier": "STUDY IDENTIFIER",
            "nct_identifier": "NCT12345678",
            "id": 1,
            "user_id": 1,
        }
    )


def factory_version() -> Version:
    return Version(**{"version": "1", "id": 1, "import_id": 1, "study_id": 1})


def factory_file_import() -> FileImport:
    return FileImport(
        **{
            "filepath": "filepath",
            "filename": "filename",
            "type": "XXX",
            "status": "Done",
            "uuid": "1234-5678",
            "id": 1,
            "user_id": 1,
            "created": datetime.datetime.now(),
        }
    )


def factory_endpoint() -> FileImport:
    return Endpoint(
        **{
            "name": "Endpoint One",
            "endpoint": "http://example.com",
            "type": "XXX",
            "id": 1,
        }
    )
