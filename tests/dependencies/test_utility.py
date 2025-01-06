from starlette.requests import Request
from starlette.datastructures import Headers
from app.dependencies.utility import admin_role_enabled, transmit_role_enabled
from tests.mocks.general_mocks import *

headers = Headers()
scope = {
    'method': 'GET',
    'type': 'http',
    'headers': headers,
    'session': {}
}

def test_admin_role_enabled():
  request = Request(scope)
  request.session['userinfo'] = {'roles': [{'name': 'Admin'}]}
  assert admin_role_enabled(request) == True

def test_is_not_admin():
  request = Request(scope)
  request.session['userinfo'] = {'roles': []}
  assert admin_role_enabled(request) == False

def test_transmit_role_enabled():
  request = Request(scope)
  request.session['userinfo'] = {'roles': [{'name': 'Transmit'}]}
  assert transmit_role_enabled(request) == True

def test_is_not_fhir_tx():
  request = Request(scope)
  request.session['userinfo'] = {'roles': []}
  assert transmit_role_enabled(request) == False
