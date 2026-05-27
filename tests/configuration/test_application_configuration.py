from app.configuration.configuration import Configuration


# Base environment mapping. Tests override individual keys as needed.
def _base_env():
    return {
        "SINGLE_USER": "false",
        "FILE_PICKER": "browser",
        "ADDRESS_SERVER_URL": "http://address.com",
        "LOCALFILE_PATH": "/local/file/path",
        "DATAFILE_PATH": "data/file/path",
        "MNT_PATH": "mount/path",
        "DATABASE_PATH": "database/path",
        "DATABASE_NAME": "databasename",
        "AUTH0_SESSION_SECRET": "secret1234",
        "CDISC_CORE_CACHE_PATH": "cache/path",
    }


def test_multiple_browser(mocker, monkeypatch):
    mock_se_get(mocker, _base_env())
    config = Configuration()
    assert not config.single_user
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
    assert config.cdisc_core_cache_path == "cache/path"


def test_single_os(mocker, monkeypatch):
    env = _base_env()
    env.update({"SINGLE_USER": "T", "FILE_PICKER": "os", "LOCALFILE_PATH": "/local/file/path/extra"})
    mock_se_get(mocker, env)
    config = Configuration()
    assert config.single_user
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
    assert config.cdisc_core_cache_path == "cache/path"


def test_single_1(mocker, monkeypatch):
    env = _base_env()
    env.update({"SINGLE_USER": "TrUe", "FILE_PICKER": "os"})
    mock_se_get(mocker, env)
    config = Configuration()
    assert config.single_user


def test_single_2(mocker, monkeypatch):
    env = _base_env()
    env.update({"SINGLE_USER": "yes", "FILE_PICKER": "os"})
    mock_se_get(mocker, env)
    config = Configuration()
    assert config.single_user


def test_single_3(mocker, monkeypatch):
    env = _base_env()
    env.update({"SINGLE_USER": "Y", "FILE_PICKER": "os"})
    mock_se_get(mocker, env)
    config = Configuration()
    assert config.single_user


def test_single_4(mocker, monkeypatch):
    env = _base_env()
    env.update({"SINGLE_USER": "Yes1", "FILE_PICKER": "os"})
    mock_se_get(mocker, env)
    config = Configuration()
    assert not config.single_user


def test_email_config_defaults(mocker, monkeypatch):
    # No SMTP/email keys provided -> sensible defaults and dev mode on.
    mock_se_get(mocker, _base_env())
    config = Configuration()
    assert config.code_length == 6
    assert config.code_expiry_minutes == 10
    assert config.smtp_port == 587
    assert config.email_dev_mode is True  # no SMTP_HOST configured
    assert config.session_secret == "secret1234"  # falls back to AUTH0_SESSION_SECRET


def test_email_config_set(mocker, monkeypatch):
    env = _base_env()
    env.update(
        {
            "SESSION_SECRET": "sess-secret",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "25",
            "SMTP_USER": "u@example.com",
            "SMTP_FROM": "noreply@example.com",
            "CODE_LENGTH": "8",
            "CODE_EXPIRY_MINUTES": "15",
            "REGISTRATION_NOTIFY_EMAIL": "admin@example.com",
        }
    )
    mock_se_get(mocker, env)
    config = Configuration()
    assert config.session_secret == "sess-secret"  # SESSION_SECRET wins over AUTH0_*
    assert config.smtp_host == "smtp.example.com"
    assert config.smtp_port == 25
    assert config.smtp_from == "noreply@example.com"
    assert config.code_length == 8
    assert config.code_expiry_minutes == 15
    assert config.email_dev_mode is False  # SMTP_HOST set
    assert config.registration_notify_email == "admin@example.com"


def mock_se_get(mocker, mapping):
    """Name-based mock so the test is robust to new config reads."""
    mock = mocker.patch("d4k_ms_base.service_environment.ServiceEnvironment.get")
    mock.side_effect = lambda name: mapping.get(name)
    return mock
