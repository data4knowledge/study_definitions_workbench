import os
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from d4kms_ui.release_notes import ReleaseNotes
from d4kms_ui.markdown_page import MarkdownPage
from app.model.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import user_details
from app.dependencies.templates import templates, templates_path
from app.dependencies.static import static_path
from app import VERSION, SYSTEM_NAME
from usdm_info import __model_version__ as usdm_version

router = APIRouter(
  prefix="/help",
  tags=["help"]
)

@router.get("/about", dependencies=[Depends(protect_endpoint)])
def about(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  rn = ReleaseNotes(os.path.join(templates_path, 'help', 'partials'))
  data = {'release_notes': rn.notes(), 'system': SYSTEM_NAME, 'version': VERSION, 'usdm': usdm_version}
  return templates.TemplateResponse(request, "help/about.html", {'user': user, 'data': data})

@router.get("/examples", dependencies=[Depends(protect_endpoint)])
def examples(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  ex = MarkdownPage('examples.md', os.path.join(templates_path, 'help', 'partials'))
  data = {'examples': ex.read()}
  return templates.TemplateResponse(request, "help/examples.html", {'user': user, 'data': data})

@router.get("/feedback", dependencies=[Depends(protect_endpoint)])
def feedback(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  fb = MarkdownPage('feedback.md', os.path.join(templates_path, 'help', 'partials'))
  data = {'feedback': fb.read()}
  return templates.TemplateResponse(request, "help/feedback.html", {'user': user, 'data': data})

@router.get("/userGuide", dependencies=[Depends(protect_endpoint)])
def logged_in_ug(request: Request, session: Session = Depends(get_db)):
  return _logged_in_document(request, "user_guide.pdf", "user guide", session)

@router.get("/userGuide/splash")
def splash_ug(request: Request):
  return _splash_document("user_guide.pdf")

@router.get("/privacyPolicy", dependencies=[Depends(protect_endpoint)])
def logged_in_pp(request: Request, session: Session = Depends(get_db)):
  return _logged_in_document(request, "privacy_policy.pdf", "privacy policy", session)

@router.get("/privacyPolicy/splash")
def splash_pp(request: Request):
  return _splash_document("privacy_policy.pdf")

def _logged_in_document(request: Request, filename: str, file_type: str, session: Session):
  user, present_in_db = user_details(request, session)
  full_path, filename, media_type =  _pdf(filename)
  print(f"PATH: {full_path}")
  if full_path:
    return FileResponse(path=full_path, filename=filename, media_type=media_type)
  else:
    return templates.TemplateResponse(request, 'errors/error.html', {'user': user, 'data': {'error': f"Error downloading the {file_type}"}})

def _splash_document(filename):
  full_path, filename, media_type =  _pdf(filename)
  if full_path:
    return FileResponse(path=full_path, filename=filename, media_type=media_type)
  else:
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

def _pdf(filename):
  media_type='text/plain'
  full_path = os.path.join(static_path, "files", filename)
  return (full_path, filename, media_type) if os.path.isfile(full_path) else (None, None, None)