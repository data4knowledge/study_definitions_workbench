from urllib.parse import quote_plus, urlencode

from fastapi import Depends, FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from d4kms_generic.auth0 import protect_endpoint, Auth0 as D4kAuth0

app = FastAPI()
templates = Jinja2Templates(directory="templates")

authorisation = D4kAuth0(app)
authorisation.register()

def protect_endpoint(request: Request) -> None:
  authorisation.protect_route(request, "/login")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login")
async def login(request: Request):
  if not 'id_token' in request.session:  # it could be userinfo instead of id_token
    return await authorisation.login(request)
  return RedirectResponse(url=app.url_path_for("profile"))

@app.get("/profile", dependencies=[Depends(protect_endpoint)])
def profile(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logout")
def logout(request: Request):
  url = authorisation.logout(request)
  return RedirectResponse(url=url)

@app.get("/callback")
async def callback(request: Request):
  try:
    await authorisation.save_token(request)
    return RedirectResponse("/profile")
  except:
    return RedirectResponse("/logout")