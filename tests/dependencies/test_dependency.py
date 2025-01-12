from fastapi import FastAPI
from tests.mocks.general_mocks import mock_called, mock_parameters_correct
from starlette.middleware.sessions import SessionMiddleware
from app.configuration.configuration import application_configuration


def test_set_middleware_secret(monkeypatch, mocker):
    # Need this to stop exception of trying to send API call on elaboration
    application_configuration.single_user = True
    from app.dependencies.dependency import set_middleware_secret

    app = FastAPI()
    application_configuration.auth0_secret = "secret"
    am = mocker.patch("fastapi.FastAPI.add_middleware")
    set_middleware_secret(app)
    assert mock_called(am)
    mock_parameters_correct(am, [mocker.call(SessionMiddleware, secret_key="secret")])
