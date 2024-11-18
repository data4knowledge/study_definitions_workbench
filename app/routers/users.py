import os
from typing import Annotated
from fastapi import APIRouter, Form, Depends, Request
from sqlalchemy.orm import Session
from app.model.user import User
from app.model.endpoint import Endpoint
from app.model.database import get_db
from app.dependencies.dependency import *
from app.dependencies.templates import templates

router = APIRouter(
  prefix="/users",
  tags=["users"],
  dependencies=[Depends(protect_endpoint)]
)

@router.get("/{id}/show")
def user_show(request: Request, id: int, session: Session = Depends(get_db)):
  user = User.find(id, session)
  user_is_admin = is_admin(request)
  data = {'endpoints': User.endpoints_page(1, 100, user.id, session), 'validation': {'user': User.valid(), 'endpoint': Endpoint.valid()}, 'debug': {'level': application_logger.get_level_str()}, 'admin': user_is_admin}
  return templates.TemplateResponse(request, "users/show.html", {'user': user, 'data': data})
  
@router.post("/{id}/displayName")
def user_display_name(request: Request, id: int, name: Annotated[str, Form()], session: Session = Depends(get_db)):
  user = User.find(id, session)
  updated_user, validation = user.update_display_name(name, session)
  use_user = updated_user if updated_user else user
  data = {'validation': {'user': validation}}
  return templates.TemplateResponse(request, f"users/partials/display_name.html", {'user': use_user, 'data': data})
  
@router.post("/{id}/endpoint")
def user_endpoint(request: Request, id: int, name: Annotated[str, Form()], url: Annotated[str, Form()], session: Session = Depends(get_db)):
  user = User.find(id, session)
  endpoint, validation = Endpoint.create(name, url, "FHIR", user.id, session)
  data = {'endpoints': User.endpoints_page(1, 100, user.id, session), 'validation': {'endpoint': validation}}
  return templates.TemplateResponse(request, f"users/partials/endpoint.html", {'user': user, 'data': data})

@router.delete("/{id}/endpoint/{endpoint_id}")
def user_endpoint(request: Request, id: int, endpoint_id: int, session: Session = Depends(get_db)):
  user = User.find(id, session)
  endpoint = Endpoint.find(endpoint_id, session)
  endpoint.delete(user.id, session)
  data = {'endpoints': User.endpoints_page(1, 100, user.id, session), 'validation': {'endpoint': Endpoint.valid()}}
  return templates.TemplateResponse(request, f"users/partials/endpoint.html", {'user': user, 'data': data})
