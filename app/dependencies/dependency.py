from fastapi import FastAPI, Request
from app.database.user import User
from d4kms_generic.auth0_service import Auth0Service
from starlette.middleware.sessions import SessionMiddleware
from app.configuration.configuration import application_configuration

def set_middleware_secret(app: FastAPI):
  app.add_middleware(SessionMiddleware, secret_key=application_configuration.auth0_secret)

def protect_endpoint(request: Request) -> None:
  if application_configuration.single_user:
    request.session['userinfo'] = User.single_user()
    return None
  else:
    authorisation.protect_route(request, "/login")

authorisation = Auth0Service()
if application_configuration.multiple_user:
  authorisation.register()
  authorisation.management_token()
