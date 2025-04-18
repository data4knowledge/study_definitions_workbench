from app.configuration.configuration import Configuration
from tests.mocks.general_mocks import *


def test_multiple_browser(mocker, monkeypatch):
    mock_se_get(
        mocker,
        [
            "false",
            "browser",
            "http://address.com",
            "/local/file/path",
            "data/file/path",
            "mount/path",
            "database/path",
            "databasename",
            "secret1234",
        ],
    )
    config = Configuration()
    assert config.single_user == False
    assert config.file_picker == {
        "browser": True,
        "os": False,
        "pfda": False,
        "source": "browser",
    }
    assert config.address_server == "http://address.com"
    assert config.local_file_path == "/local/file/path"
    assert config.data_file_path == "data/file/path"
    assert config.mount_path == "mount/path"
    assert config.database_path == "database/path"
    assert config.database_name == "databasename"
    assert config.auth0_secret == "secret1234"


def test_single_os(mocker, monkeypatch):
    mock_se_get(
        mocker,
        [
            "T",
            "os",
            "http://address.com",
            "/local/file/path/extra",
            "data/file/path",
            "mount/path",
            "database/path",
            "databasename",
            "secret1234",
        ],
    )
    config = Configuration()
    assert config.single_user == True
    assert config.file_picker == {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    assert config.address_server == "http://address.com"
    assert config.local_file_path == "/local/file/path/extra"
    assert config.data_file_path == "data/file/path"
    assert config.mount_path == "mount/path"
    assert config.database_path == "database/path"
    assert config.database_name == "databasename"
    assert config.auth0_secret == "secret1234"


def test_single_1(mocker, monkeypatch):
    mock_se_get(
        mocker,
        [
            "TrUe",
            "os",
            "http://address.com",
            "/local/file/path/extra",
            "data/file/path",
            "mount/path",
            "database/path",
            "databasename",
            "secret1234",
        ],
    )
    config = Configuration()
    assert config.single_user == True


def test_single_2(mocker, monkeypatch):
    mock_se_get(
        mocker,
        [
            "yes",
            "os",
            "http://address.com",
            "/local/file/path/extra",
            "data/file/path",
            "mount/path",
            "database/path",
            "databasename",
            "secret1234",
        ],
    )
    config = Configuration()
    assert config.single_user == True


def test_single_3(mocker, monkeypatch):
    mock_se_get(
        mocker,
        [
            "Y",
            "os",
            "http://address.com",
            "/local/file/path/extra",
            "data/file/path",
            "mount/path",
            "database/path",
            "databasename",
            "secret1234",
        ],
    )
    config = Configuration()
    assert config.single_user == True


def test_single_3(mocker, monkeypatch):
    mock_se_get(
        mocker,
        [
            "Yes1",
            "os",
            "http://address.com",
            "/local/file/path/extra",
            "data/file/path",
            "mount/path",
            "database/path",
            "databasename",
            "secret1234",
        ],
    )
    config = Configuration()
    assert config.single_user == False


def mock_se_get(mocker, value):
    mock = mocker.patch("d4k_ms_base.service_environment.ServiceEnvironment.get")
    mock.side_effect = value
    return mock
