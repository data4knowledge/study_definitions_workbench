from urllib.parse import quote_plus, urlencode

from fastapi import Depends, FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from d4kms_generic.auth0_service import Auth0Service
from d4kms_generic import application_logger

VERSION = '0.3'
SYSTEM_NAME = "d4k Study Definitions Workbench"

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

@app.get("/")
def home(request: Request):
  response = templates.TemplateResponse('home/home.html', {"request": request, "version": VERSION})
  return response

# @app.get("/")
# def home(request: Request):
#     return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login")
async def login(request: Request):
  if not 'id_token' in request.session:  # it could be userinfo instead of id_token
    return await authorisation.login(request, "callback")
  return RedirectResponse("/index")

@app.get("/index", dependencies=[Depends(protect_endpoint)])
def index(request: Request):
  return templates.TemplateResponse("home/index.html", {"request": request})

@app.get("/test1", dependencies=[Depends(protect_endpoint)])
def test1(request: Request):
  return templates.TemplateResponse("home/test1.html", {"request": request})

@app.get("/test2", dependencies=[Depends(protect_endpoint)])
def test2(request: Request):
  return templates.TemplateResponse("home/test2.html", {"request": request})

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