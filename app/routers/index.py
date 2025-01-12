import json
from fastapi import APIRouter, Form, Depends, Request
from sqlalchemy.orm import Session
from app.database.study import Study
from app.database.user import User
from d4kms_ui.pagination import Pagination
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.templates import templates
from app.dependencies.utility import transmit_role_enabled, user_details
from app.dependencies.fhir_version import fhir_versions
from d4kms_generic.logger import application_logger

COOKIE = "index_filter"

router = APIRouter(prefix="", tags=["index"], dependencies=[Depends(protect_endpoint)])


@router.get("/index")
def index(request: Request, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    fhir = {"enabled": transmit_role_enabled(request), "versions": fhir_versions()}
    if present_in_db or user:
        data = {"fhir": fhir}
        return templates.TemplateResponse(
            request, "home/index.html", {"user": user, "data": data}
        )
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {"user": None, "data": {"error": "Unable to determine user."}},
        )


@router.get("/index/page")
def index_page(
    request: Request,
    page: int,
    size: int,
    initial: bool = False,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    data = {}
    cookie, params = _cookie_and_params(initial, request, user, session)
    data["page"] = Study.page(page, size, user.id, params, session)
    data["width"] = 4
    data["index_filter"] = cookie
    pagination = Pagination(data["page"], "/index/page")
    response = templates.TemplateResponse(
        request,
        "home/partials/page.html",
        {"user": user, "pagination": pagination, "data": data},
    )
    _set_cookie(response, cookie)
    return response


@router.post("/index/filter")
def index_page(
    request: Request,
    filter_type: str,
    id: int,
    state: bool,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    data = _get_cookie(request, user, session)
    data[filter_type][id]["selected"] = state
    response = templates.TemplateResponse(request, "home/partials/empty.html")
    _set_cookie(response, data)
    return response


def _cookie_and_params(
    initial: bool, request: Request, user: User, session: Session
) -> tuple[dict, dict]:
    params = {}
    if initial:
        cookie = _base_cookie(user, session)
    else:
        cookie = _get_cookie(request, user, session)
        all_true = all([x["selected"] for x in cookie["phase"]]) and all(
            [x["selected"] for x in cookie["sponsor"]]
        )
        params = {
            "phase": [x["label"] for x in cookie["phase"] if x["selected"]],
            "sponsor": [x["label"] for x in cookie["sponsor"] if x["selected"]],
        }
        params = params if not all_true else {}
    return cookie, params


def _get_cookie(request: Request, user: User, session: Session) -> dict:
    default = json.dumps(_base_cookie(user, session))
    cookie = json.loads(request.cookies.get(COOKIE, default))
    # application_logger.debug(f"Index filter cookie get {cookie}")
    return cookie


def _set_cookie(response, cookie: dict) -> None:
    # application_logger.debug(f"Index filter cookie set {cookie}")
    response.set_cookie(COOKIE, value=json.dumps(cookie), httponly=True, expires=3600)


def _base_cookie(user: User, session: Session) -> dict:
    return {
        "phase": [
            {"selected": True, "label": x, "index": i}
            for i, x in enumerate(Study.phases(user.id, session))
        ],
        "sponsor": [
            {"selected": True, "label": x, "index": i}
            for i, x in enumerate(Study.sponsors(user.id, session))
        ],
    }
