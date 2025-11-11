import json
import pytest
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import (
    mock_user_check_exists,
    mock_user_check_new,
    mock_user_check_fail,
)
from tests.mocks.fastapi_mocks import protect_endpoint, mock_client


@pytest.fixture
def anyio_backend():
    return "asyncio"


# Tests
def test_index_no_user(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_fail(mocker)
    response = client.get("/index")
    assert response.status_code == 200
    assert """Unable to determine user.""" in response.text


def test_index_new_user(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_new(mocker)
    response = client.get("/index")
    assert response.status_code == 200
    assert """Loading...""" in response.text


def test_index_existing_user_none(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    response = client.get("/index")
    assert response.status_code == 200
    assert """Loading...""" in response.text


def test_index_existing_user_studies(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    response = client.get("/index")
    assert response.status_code == 200
    assert """Loading...""" in response.text


def test_index_page_none(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    sp = mock_study_page_none(mocker)
    response = client.get("/index/page?page=1&size=5&initial=true")
    assert response.status_code == 200
    assert """You have not loaded any studies yet.""" in response.text
    assert mock_called(sp)
    assert sp.mock_calls[0].args[0] == 1
    assert sp.mock_calls[0].args[1] == 5
    assert sp.mock_calls[0].args[2] == 1


def test_index_page(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    sp = mock_study_page(mocker)
    response = client.get("/index/page?page=2&size=10&initial=true")
    assert response.status_code == 200
    assert """View Protocol""" in response.text
    assert """A study for Z""" in response.text
    assert mock_called(sp)
    assert sp.mock_calls[0].args[0] == 2
    assert sp.mock_calls[0].args[1] == 10
    assert sp.mock_calls[0].args[2] == 1


def test_index_pagination(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    sp = mock_study_page_many(mocker)
    response = client.get("/index/page?page=1&size=12&initial=true")
    # print(f"RESPONSE: {response.text}")
    assert response.status_code == 200
    assert """View Protocol""" in response.text
    assert """A study for X""" in response.text
    assert (
        """<a class="dropdown-item" href="#" hx-get="/index/page?page=1&amp;size=96" hx-trigger="click" hx-target="#data_div" hx-swap="outerHTML">96</a>"""
        in response.text
    )
    assert (
        """<button class="btn btn-sm btn-outline-primary rounded-5 mb-1  " href="#" hx-get="/index/page?page=4&amp;size=12&amp;filter=" hx-trigger="click" hx-target="#data_div" hx-swap="outerHTML">4</a>"""
        in response.text
    )
    assert (
        """<button class="btn btn-sm btn-outline-primary rounded-5 mb-1  disabled" href="#" hx-get="" hx-trigger="click" hx-target="#data_div" hx-swap="outerHTML">...</a>"""
        in response.text
    )
    assert mock_called(sp)


def test_index_filter_no_cookie(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    sp = mock_study_phases(mocker)
    ss = mock_study_sponsors(mocker)
    response = client.post("/index/filter?filter_type=phase&id=0&state=false")
    raw_cookie = string_escape(response.cookies["index_filter"])[
        1:-1
    ]  # Remove leading and trailing doubel quote characters
    received_cookie = json.loads(raw_cookie)
    assert response.status_code == 200
    assert """<div id="filterSelectedDiv"></div>""" in response.text
    assert received_cookie == {
        "phase": [
            {"selected": False, "label": "Phase 1", "index": 0},
            {"selected": True, "label": "Phase 4", "index": 1},
        ],
        "sponsor": [
            {"selected": True, "label": "ACME", "index": 0},
            {"selected": True, "label": "Big Pharma", "index": 1},
        ],
    }
    assert mock_called(sp)
    assert mock_called(ss)


def test_index_filter(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    cookie = base_cookie()
    cookie["phase"][1]["selected"] = False
    cookie["sponsor"][0]["selected"] = False
    client.cookies = {"index_filter": json.dumps(cookie)}
    response = client.post("/index/filter?filter_type=phase&id=0&state=false")
    raw_cookie = string_escape(response.cookies["index_filter"])[
        1:-1
    ]  # Remove leading and trailing doubel quote characters
    received_cookie = json.loads(raw_cookie)
    assert response.status_code == 200
    assert """<div id="filterSelectedDiv"></div>""" in response.text
    assert received_cookie == {
        "phase": [
            {"selected": False, "label": "Phase 1", "index": 0},
            {"selected": False, "label": "Phase 4", "index": 1},
        ],
        "sponsor": [
            {"selected": False, "label": "ACME", "index": 0},
            {"selected": True, "label": "Big Pharma", "index": 1},
        ],
    }


def string_escape(s: str, encoding="utf-8"):
    return (
        s.encode("latin1")  # To bytes, required by 'unicode-escape'
        .decode("unicode-escape")  # Perform the actual octal-escaping decode
        .encode("latin1")  # 1:1 mapping back to bytes
        .decode(encoding)
    )  # Decode original encoding


# Mocks
def mock_study_page_none(mocker):
    mock = mocker.patch("app.database.study.Study.page")
    mock.side_effect = [{"page": 1, "size": 10, "count": 0, "filter": "", "items": []}]
    return mock


def mock_study_page(mocker):
    mock = mocker.patch("app.database.study.Study.page")
    items = [
        {
            "sponsor": "ACME",
            "sponsor_identifier": "ACME",
            "title": "A study for X",
            "versions": 1,
            "phase": "Phase 1",
            "import_type": "DOCX",
        },
        {
            "sponsor": "Big Pharma",
            "sponsor_identifier": "BP",
            "title": "A study for Y",
            "versions": 2,
            "phase": "Phase 1",
            "import_type": "XLSX",
        },
        {
            "sponsor": "Big Pharma",
            "sponsor_identifier": "BP",
            "title": "A study for Z",
            "versions": 3,
            "phase": "Phase 4",
            "import_type": "FHIR",
        },
    ]
    mock.side_effect = [
        {"page": 1, "size": 12, "count": 3, "filter": "", "items": items}
    ]
    return mock


def mock_study_page_many(mocker):
    items = []
    mock = mocker.patch("app.database.study.Study.page")
    for index in range(12):
        items.append(
            {
                "sponsor": "ACME",
                "sponsor_identifier": "ACME",
                "title": "A study for X",
                "versions": 1,
                "phase": "Phase 1",
                "import_type": "DOCX",
            }
        )
    mock.side_effect = [
        {"page": 1, "size": 12, "count": 100, "filter": "", "items": items}
    ]
    return mock


def mock_study_phases(mocker):
    mock = mocker.patch("app.database.study.Study.phases")
    mock.side_effect = [["Phase 1", "Phase 4"]]
    return mock


def mock_study_sponsors(mocker):
    mock = mocker.patch("app.database.study.Study.sponsors")
    mock.side_effect = [["ACME", "Big Pharma"]]
    return mock


def mock_study_phases_many(mocker):
    mock = mocker.patch("app.database.study.Study.phases")
    mock.side_effect = [["Phase 1"]]
    return mock


def mock_study_sponsors_many(mocker):
    mock = mocker.patch("app.database.study.Study.sponsors")
    mock.side_effect = [["ACME"]]
    return mock


def base_cookie():
    return {
        "phase": [
            {"selected": True, "label": "Phase 1", "index": 0},
            {"selected": True, "label": "Phase 4", "index": 1},
        ],
        "sponsor": [
            {"selected": True, "label": "ACME", "index": 0},
            {"selected": True, "label": "Big Pharma", "index": 1},
        ],
    }
