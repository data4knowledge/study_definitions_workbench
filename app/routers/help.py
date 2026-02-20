import os
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from d4k_ms_ui.release_notes import ReleaseNotes
from d4k_ms_ui.markdown_page import MarkdownPage
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import user_details
from app.dependencies.templates import templates, templates_path
from app import VERSION, SYSTEM_NAME
from usdm_info import __model_version__ as usdm_version

router = APIRouter(prefix="/help", tags=["help"])
PARTIALS_PATH = os.path.join(templates_path, "help", "partials")


@router.get("/about", dependencies=[Depends(protect_endpoint)])
def about(request: Request, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    rn = ReleaseNotes(PARTIALS_PATH)
    data = {
        "release_notes": rn.notes(),
        "system": SYSTEM_NAME,
        "version": VERSION,
        "usdm": usdm_version,
    }
    return templates.TemplateResponse(
        request, "help/about.html", {"user": user, "data": data}
    )


@router.get("/examples", dependencies=[Depends(protect_endpoint)])
def examples(request: Request, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    ex = MarkdownPage("examples.md", PARTIALS_PATH)
    data = {"examples": ex.read()}
    return templates.TemplateResponse(
        request, "help/examples.html", {"user": user, "data": data}
    )


@router.get("/feedback", dependencies=[Depends(protect_endpoint)])
def feedback(request: Request, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    fb = MarkdownPage("feedback.md", PARTIALS_PATH)
    data = {"feedback": fb.read()}
    return templates.TemplateResponse(
        request, "help/feedback.html", {"user": user, "data": data}
    )


@router.get("/userGuide", dependencies=[Depends(protect_endpoint)])
def logged_in_ug(request: Request, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    ug = MarkdownPage("user_guide.md", PARTIALS_PATH)
    data = {"user_guide": ug.read()}
    return templates.TemplateResponse(
        request, "help/user_guide.html", {"user": user, "data": data}
    )


@router.get("/userGuide/splash")
def splash_ug(request: Request):
    ug = MarkdownPage("user_guide.md", PARTIALS_PATH)
    data = {"user_guide": ug.read()}
    return templates.TemplateResponse(
        request, "help/user_guide_splash.html", {"data": data}
    )


@router.get("/privacyPolicy", dependencies=[Depends(protect_endpoint)])
def logged_in_pp(request: Request, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    pp = MarkdownPage("privacy_policy.md", PARTIALS_PATH)
    data = {"privacy_policy": pp.read()}
    return templates.TemplateResponse(
        request, "help/privacy_policy.html", {"user": user, "data": data}
    )


@router.get("/privacyPolicy/splash")
def splash_pp(request: Request):
    pp = MarkdownPage("privacy_policy.md", PARTIALS_PATH)
    data = {"privacy_policy": pp.read()}
    return templates.TemplateResponse(
        request, "help/privacy_policy_splash.html", {"data": data}
    )


@router.get("/prism", dependencies=[Depends(protect_endpoint)])
def prism(request: Request, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    pr = MarkdownPage("prism.md", PARTIALS_PATH)
    data = {"prism": pr.read()}
    return templates.TemplateResponse(
        request, "help/prism.html", {"user": user, "data": data}
    )
