from urllib.parse import quote_plus, urlencode

from fastapi import Depends, FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from d4kms_generic.auth0_service import Auth0Service
from d4kms_generic import application_logger
from d4kms_ui.release_notes import ReleaseNotes
from model.database import SessionLocal, engine, get_db
from model.user import User, UserCreate
from sqlalchemy.orm import Session
from model import models

VERSION = '0.4'
SYSTEM_NAME = "d4k Study Definitions Workbench"

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
  title = SYSTEM_NAME,
  description = "d4k Study Definitions Workbench. The Swiss Army Knife for DDF / USDM Study Definitions",
  version = VERSION
)

application_logger.info(f"Starting {SYSTEM_NAME}")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

authorisation = Auth0Service(app)
authorisation.register()

def protect_endpoint(request: Request) -> None:
  authorisation.protect_route(request, "/login")

def user_details(request: Request, db):
  user_info = request.session['userinfo']
  user, present_in_db = User.check(user_info['email'], db)
  return user, present_in_db

@app.get("/")
def home(request: Request):
  response = templates.TemplateResponse('home/home.html', {'request': request, "version": VERSION})
  return response

@app.get("/login")
async def login(request: Request):
  if not 'id_token' in request.session:  # it could be userinfo instead of id_token
    return await authorisation.login(request, "callback")
  return RedirectResponse("/index")

@app.get("/index", dependencies=[Depends(protect_endpoint)])
def index(request: Request, db: Session = Depends(get_db)):
  user, present_in_db = user_details(request, db)
  if present_in_db:
    return templates.TemplateResponse("home/index.html", {'request': request, 'user': user})
  else:
    return templates.TemplateResponse("user/edit.html", {'request': request, 'user': user})

@app.get("/users/{id}/show", dependencies=[Depends(protect_endpoint)])
def user_show(request: Request, id: int, db: Session = Depends(get_db)):
  user = User.find(id, db)
  return templates.TemplateResponse("users/show.html", {'request': request, 'user': user})

@app.post("/users/{id}/displayName", dependencies=[Depends(protect_endpoint)])
def user_display_name(request: Request, id: int, db: Session = Depends(get_db)):
  user = User.find(id, db)
  return templates.TemplateResponse(f"users/partials/displayName.html", {'request': request, 'user': user})

@app.get("/about", dependencies=[Depends(protect_endpoint)])
def user_show(request: Request, db: Session = Depends(get_db)):
  user, present_in_db = user_details(request, db)
  data = {'release_notes': ReleaseNotes().notes(), 'system': SYSTEM_NAME, 'version': VERSION}
  return templates.TemplateResponse("about/about.html", {'request': request, 'user': user, 'data': data})

@app.get("/import/m11", dependencies=[Depends(protect_endpoint)])
def user_show(request: Request, db: Session = Depends(get_db)):
  user, present_in_db = user_details(request, db)
  return templates.TemplateResponse("import/import_m11.html", {'request': request, 'user': user})

@app.get("/import/xl", dependencies=[Depends(protect_endpoint)])
def user_show(request: Request, db: Session = Depends(get_db)):
  user, present_in_db = user_details(request, db)
  return templates.TemplateResponse("import/import_xl.html", {'request': request, 'user': user})

@app.get("/logout")
def logout(request: Request):
  url = authorisation.logout(request, "home")
  return RedirectResponse(url=url)

@app.get("/callback")
async def callback(request: Request):
  try:
    await authorisation.save_token(request)
    return RedirectResponse("/index")
  except:
    return RedirectResponse("/logout")