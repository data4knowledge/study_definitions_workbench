from starlette.requests import Request
from starlette.datastructures import Headers
from app.dependencies.utility import admin_role_enabled, transmit_role_enabled

headers = Headers()
scope = {"method": "GET", "type": "http", "headers": headers, "session": {}}


def test_admin_role_enabled():
    request = Request(scope)
    request.session["userinfo"] = {"roles": [{"name": "Admin"}]}
    assert admin_role_enabled(request)


def test_is_not_admin():
    request = Request(scope)
    request.session["userinfo"] = {"roles": []}
    assert not admin_role_enabled(request)


def test_transmit_role_enabled():
    request = Request(scope)
    request.session["userinfo"] = {"roles": [{"name": "Transmit"}]}
    assert transmit_role_enabled(request)


def test_is_not_fhir_tx():
    request = Request(scope)
    request.session["userinfo"] = {"roles": []}
    assert not transmit_role_enabled(request)
