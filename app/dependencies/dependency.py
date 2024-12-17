from fastapi import FastAPI, Request
from app.dependencies.utility import single_user
from app.database.user import User
from d4kms_generic.auth0_service import Auth0Service
from d4kms_generic.service_environment import ServiceEnvironment
from starlette.middleware.sessions import SessionMiddleware

def set_middleware_secret(app: FastAPI):
  se = ServiceEnvironment()
  secret = se.get('AUTH0_SESSION_SECRET')
  app.add_middleware(SessionMiddleware, secret_key=secret)

def protect_endpoint(request: Request) -> None:
  if single_user():
    request.session['userinfo'] = User.single_user()
    return None
  else:
    authorisation.protect_route(request, "/login")

authorisation = Auth0Service()
if not single_user():
  authorisation.register()
  authorisation.management_token()
