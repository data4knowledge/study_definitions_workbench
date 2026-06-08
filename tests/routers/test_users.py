import pytest
from unittest.mock import MagicMock
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import (
    mock_user_endpoints_page,
    mock_user_valid,
    mock_endpoint_valid,
    mock_user_update_display_name,
    mock_endpoint_create,
    mock_user_find,
)
from tests.mocks.fastapi_mocks import protect_endpoint, mock_client
from tests.mocks.factory_mocks import factory_user


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_user_show(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uf = mock_user_find(mocker)
    uep = mock_user_endpoints_page(mocker)
    uv = mock_user_valid(mocker)
    ev = mock_endpoint_valid(mocker)
    response = client.get("/users/1/show")
    assert response.status_code == 200
    assert """Enter a new display name""" in response.text
    assert mock_called(uf)
    assert mock_called(uv)
    assert mock_called(uep)
    assert mock_called(ev)


def test_user_update_display_name(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uf = mock_user_find(mocker)
    uudn = mock_user_update_display_name(mocker)
    response = client.post(
        "/users/1/displayName",
        data={"name": "Smithy"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert """Fred Smithy""" in response.text
    assert mock_called(uf)
    assert mock_called(uudn)


def test_user_update_display_name_error(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uf = mock_user_find(mocker)
    uudn = mock_user_update_display_name(mocker)
    uudn.side_effect = [
        (
            None,
            {
                "display_name": {"valid": True, "message": ""},
                "email": {"valid": True, "message": ""},
                "identifier": {"valid": True, "message": ""},
            },
        )
    ]
    response = client.post(
        "/users/1/displayName",
        data={"name": "Smithy"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert """Fred Smith""" in response.text
    assert mock_called(uf)


def test_user_endpoint(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uf = mock_user_find(mocker)
    ec = mock_endpoint_create(mocker)
    uep = mock_user_endpoints_page(mocker)
    uep.side_effects = [{"page": 1, "size": 10, "count": 0, "filter": "", "items": []}]
    response = client.post(
        "/users/1/endpoint",
        data={"name": "Smithy", "url": "http://"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert """Enter a name for the server""" in response.text
    assert mock_called(uf)
    assert mock_called(ec)


def test_delete_user_endpoint(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uf = mock_user_find(mocker)
    ep_find = mocker.patch("app.database.endpoint.Endpoint.find")
    ep_find.return_value = MagicMock()
    ev = mock_endpoint_valid(mocker)
    mock_user_endpoints_page(mocker)
    response = client.delete("/users/1/endpoint/1")
    assert response.status_code == 200
    assert mock_called(uf)
    assert mock_called(ev)


# --- User administration (roles) ---


def test_manage_users_admin(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mocker.patch("app.routers.users.admin_role_enabled", return_value=True)
    mocker.patch("app.routers.users.user_details", return_value=(factory_user(), True))
    mocker.patch("app.database.user.User.list_all", return_value=[factory_user()])
    response = client.get("/users/manage")
    assert response.status_code == 200
    assert "User Administration" in response.text
    assert "fred@example.com" in response.text


def test_manage_users_not_admin(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mocker.patch("app.routers.users.admin_role_enabled", return_value=False)
    response = client.get("/users/manage", follow_redirects=False)
    assert response.status_code == 303
    assert str(response.next_request.url) == "http://testserver/index"


def test_update_user_roles_admin(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mocker.patch("app.routers.users.admin_role_enabled", return_value=True)
    uf = mock_user_find(mocker)
    sr = mocker.patch("app.database.user.User.set_roles", return_value=factory_user())
    response = client.post(
        "/users/1/roles",
        data={"admin": "on"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "fred@example.com" in response.text
    assert mock_called(uf)
    assert mock_called(sr)


def test_update_user_roles_not_admin(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mocker.patch("app.routers.users.admin_role_enabled", return_value=False)
    response = client.post(
        "/users/1/roles",
        data={"admin": "on"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert str(response.next_request.url) == "http://testserver/index"
