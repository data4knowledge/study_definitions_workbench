#import os
from fastapi import FastAPI, Request
from app.model.user import User
from d4kms_generic.auth0_service import Auth0Service
from d4kms_generic import application_logger
from d4kms_generic.service_environment import ServiceEnvironment
from starlette.middleware.sessions import SessionMiddleware

def set_middleware_secret(app: FastAPI):
  se = ServiceEnvironment()
  secret = se.get('AUTH0_SESSION_SECRET')
  app.add_middleware(SessionMiddleware, secret_key=secret)

def single_user() -> bool:
  se = ServiceEnvironment()
  single = se.get('SINGLE_USER')
  application_logger.info(f"Single user mode '{single}'")
  return single.upper() in ['TRUE', 'Y', 'YES']

def protect_endpoint(request: Request) -> None:
  if single_user():
    request.session['userinfo'] = User.single_user()
    return None
  else:
    authorisation.protect_route(request, "/login")

def user_details(request: Request, db):
  user_info = request.session['userinfo']
  user, present_in_db = User.check(user_info, db)
  return user, present_in_db

def is_admin(request: Request):
  user_info = request.session['userinfo']
  admin = next((x for x in user_info['roles'] if x['name'] == 'Admin'), None)
  return True if admin else False

authorisation = Auth0Service()
if not single_user():
  authorisation.register()
  authorisation.management_token()
