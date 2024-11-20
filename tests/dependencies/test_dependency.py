from fastapi import FastAPI
from tests.mocks.general_mocks import mock_called, mock_parameters_correct
from starlette.middleware.sessions import SessionMiddleware

def test_set_middleware_secret(monkeypatch, mocker):

  # Need this to stop exception of trying to send API call on elaborationpytes
  monkeypatch.setenv("SINGLE_USER", "True")
  from app.dependencies.dependency import set_middleware_secret

  app = FastAPI()
  monkeypatch.setenv("AUTH0_SESSION_SECRET", "secret")
  am = mocker.patch("fastapi.FastAPI.add_middleware")
  set_middleware_secret(app)
  assert mock_called(am)
  mock_parameters_correct(am, [mocker.call(SessionMiddleware, secret_key='secret')])