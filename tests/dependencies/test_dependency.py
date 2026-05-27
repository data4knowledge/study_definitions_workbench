import pytest
from fastapi import FastAPI, HTTPException
from tests.mocks.general_mocks import mock_called, mock_parameters_correct
from starlette.middleware.sessions import SessionMiddleware
from app.configuration.configuration import application_configuration


class _Req:
    """Minimal stand-in for a Starlette Request with a session dict."""

    def __init__(self, session=None):
        self.session = session if session is not None else {}


def test_protect_endpoint_single_user_injects_userinfo():
    from app.dependencies.dependency import protect_endpoint

    application_configuration.single_user = True
    request = _Req()
    assert protect_endpoint(request) is None
    # Single user is always Admin + Transmit.
    assert request.session["userinfo"]["roles"] == [
        {"name": "Admin"},
        {"name": "Transmit"},
    ]
    assert request.session["userinfo"]["sub"] == "SUE|1234567890"


def test_protect_endpoint_multiple_user_not_logged_in_redirects():
    from app.dependencies.dependency import protect_endpoint

    application_configuration.single_user = False
    request = _Req()
    with pytest.raises(HTTPException) as exc:
        protect_endpoint(request)
    assert exc.value.status_code == 307
    assert exc.value.headers["Location"] == "/login"


def test_protect_endpoint_multiple_user_logged_in_passes():
    from app.dependencies.dependency import protect_endpoint

    application_configuration.single_user = False
    request = _Req(session={"userinfo": {"email": "x@y.com", "roles": []}})
    assert protect_endpoint(request) is None


def test_set_middleware_secret(monkeypatch, mocker):
    # Need this to stop exception of trying to send API call on elaboration
    application_configuration.single_user = True
    from app.dependencies.dependency import set_middleware_secret

    app = FastAPI()
    application_configuration.session_secret = "secret"
    am = mocker.patch("fastapi.FastAPI.add_middleware")
    set_middleware_secret(app)
    assert mock_called(am)
    mock_parameters_correct(am, [mocker.call(SessionMiddleware, secret_key="secret")])
