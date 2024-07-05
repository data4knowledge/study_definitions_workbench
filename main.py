from urllib.parse import quote_plus, urlencode

from fastapi import Depends, FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from d4kms_generic.auth0 import Auth0 as D4kAuth0

app = FastAPI()
templates = Jinja2Templates(directory="templates")

authorisation = D4kAuth0(app)
authorisation.register()

def get_abs_path(route: str):
  app_domain = "http://localhost:8000"
  return f"{app_domain}{app.url_path_for(route)}"

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login(request: Request):
  if not 'id_token' in request.session:  # it could be userinfo instead of id_token
    return await authorisation.oauth.auth0.authorize_redirect(
        request,
        redirect_uri=get_abs_path("callback"),
        audience=authorisation.audience
    )
  return RedirectResponse(url=app.url_path_for("profile"))

@app.get("/profile", dependencies=[Depends(authorisation.protect_endpoint)])
def profile(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logout")
def logout(request: Request):
    data = {"returnTo": get_abs_path("home"),"client_id": authorisation.client_id}
    response = RedirectResponse(
        url=f"https://{authorisation.domain}/v2/logout?{urlencode(data,quote_via=quote_plus,)}")
    request.session.clear()
    return response

@app.get("/callback")
async def callback(request: Request):
  token = await authorisation.oauth.auth0.authorize_access_token(request)
  # Store `access_token`, `id_token`, and `userinfo` in session
  request.session['access_token'] = token['access_token']
  request.session['id_token'] = token['id_token']
  request.session['userinfo'] = token['userinfo']
  return RedirectResponse("/profile")