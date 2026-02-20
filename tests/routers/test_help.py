import pytest
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import mock_user_check_exists
from tests.mocks.fastapi_mocks import protect_endpoint, mock_client


@pytest.fixture
def anyio_backend():
    return "asyncio"


# Tests
def test_about(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    mock_release_notes(mocker)
    response = client.get("/help/about")
    assert response.status_code == 200
    assert """Release Notes Test Testy""" in response.text
    assert mock_called(uc)


def test_examples(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    mock_markdown_page(mocker, "Examples Test Testy")
    response = client.get("/help/examples")
    assert response.status_code == 200
    assert """Examples Test Testy""" in response.text
    assert mock_called(uc)


def test_feedback(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    mock_markdown_page(mocker, "Feedback Test Testy Testy")
    response = client.get("/help/feedback")
    assert response.status_code == 200
    assert """Feedback Test Testy Testy""" in response.text
    assert mock_called(uc)


def test_user_guide(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    mock_markdown_page(mocker, "User Guide Test Content")
    response = client.get("/help/userGuide")
    assert response.status_code == 200
    assert """User Guide Test Content""" in response.text
    assert mock_called(uc)


def test_user_guide_splash(mocker, monkeypatch):
    client = mock_client(monkeypatch)
    mock_markdown_page(mocker, "User Guide Splash Content")
    response = client.get("/help/userGuide/splash")
    assert response.status_code == 200
    assert """User Guide Splash Content""" in response.text


def test_privacy(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    mock_markdown_page(mocker, "Privacy Policy Test Content")
    response = client.get("/help/privacyPolicy")
    assert response.status_code == 200
    assert """Privacy Policy Test Content""" in response.text
    assert mock_called(uc)


def test_privacy_splash(mocker, monkeypatch):
    client = mock_client(monkeypatch)
    mock_markdown_page(mocker, "Privacy Policy Splash Content")
    response = client.get("/help/privacyPolicy/splash")
    assert response.status_code == 200
    assert """Privacy Policy Splash Content""" in response.text


def test_prism(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    mock_markdown_page(mocker, "PRISM Guide Test Content")
    response = client.get("/help/prism")
    assert response.status_code == 200
    assert """PRISM Guide Test Content""" in response.text
    assert mock_called(uc)


# Mocks
def mock_release_notes(mocker):
    rn = mocker.patch("d4k_ms_ui.ReleaseNotes.__init__")
    rn.side_effect = [None]
    rnn = mocker.patch("d4k_ms_ui.ReleaseNotes.notes")
    rnn.side_effect = ["Release Notes Test Testy"]


def mock_markdown_page(mocker, content):
    mp = mocker.patch("d4k_ms_ui.MarkdownPage.__init__")
    mp.side_effect = [None]
    mpr = mocker.patch("d4k_ms_ui.MarkdownPage.read")
    mpr.side_effect = [content]
