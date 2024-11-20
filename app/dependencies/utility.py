from fastapi import Request
from app.model.user import User
from d4kms_generic import application_logger
from d4kms_generic.service_environment import ServiceEnvironment

def single_user() -> bool:
  se = ServiceEnvironment()
  single = se.get('SINGLE_USER')
  application_logger.info(f"Single user mode '{single}'")
  return single.upper() in ['TRUE', 'Y', 'YES']

def user_details(request: Request, db):
  user_info = request.session['userinfo']
  user, present_in_db = User.check(user_info, db)
  return user, present_in_db

def is_admin(request: Request):
  user_info = request.session['userinfo']
  role = next((x for x in user_info['roles'] if x['name'] == 'Admin'), None)
  return True if role else False

def is_fhir_tx(request: Request):
  user_info = request.session['userinfo']
  role = next((x for x in user_info['roles'] if x['name'] == 'FHIR-Tx'), None)
  return True if role else False
