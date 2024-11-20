from starlette.requests import Request
from starlette.datastructures import Headers
from app.dependencies.utility import is_admin, is_fhir_tx
from tests.mocks.general_mocks import *

headers = Headers()
scope = {
    'method': 'GET',
    'type': 'http',
    'headers': headers,
    'session': {}
}

def test_is_admin():
  request = Request(scope)
  request.session['userinfo'] = {'roles': [{'name': 'Admin'}]}
  assert is_admin(request) == True

def test_is_not_admin():
  request = Request(scope)
  request.session['userinfo'] = {'roles': []}
  assert is_admin(request) == False

def test_is_fhir_tx():
  request = Request(scope)
  request.session['userinfo'] = {'roles': [{'name': 'FHIR-Tx'}]}
  assert is_fhir_tx(request) == True

def test_is_not_fhir_tx():
  request = Request(scope)
  request.session['userinfo'] = {'roles': []}
  assert is_fhir_tx(request) == False
