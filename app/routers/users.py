from typing import Annotated, Optional
from fastapi import APIRouter, Form, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database.user import User
from app.database.endpoint import Endpoint
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import admin_role_enabled, user_details
from app.dependencies.templates import templates
from d4k_ms_base.logger import application_logger

router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(protect_endpoint)]
)


@router.get("/manage")
def manage_users(request: Request, session: Session = Depends(get_db)):
    """Admin-only screen to grant/revoke Admin and Transmit roles."""
    if not admin_role_enabled(request):
        return RedirectResponse("/index", status_code=status.HTTP_303_SEE_OTHER)
    current_user, _ = user_details(request, session)
    data = {"users": User.list_all(session), "admin_domain": User.ADMIN_DOMAIN}
    return templates.TemplateResponse(
        request, "users/manage.html", {"user": current_user, "data": data}
    )


@router.post("/{id}/roles")
def update_user_roles(
    request: Request,
    id: int,
    admin: Optional[str] = Form(None),
    transmit: Optional[str] = Form(None),
    session: Session = Depends(get_db),
):
    """Update a user's stored roles. Admin only; rendered as an HTMX row."""
    if not admin_role_enabled(request):
        return RedirectResponse("/index", status_code=status.HTTP_303_SEE_OTHER)
    user = User.find(id, session)
    roles = []
    if admin:
        roles.append("Admin")
    if transmit:
        roles.append("Transmit")
    user = user.set_roles(roles, session)
    application_logger.info(f"Roles for '{user.email}' set to '{user.roles}'")
    return templates.TemplateResponse(
        request,
        "users/partials/user_row.html",
        {"u": user, "saved": True, "admin_domain": User.ADMIN_DOMAIN},
    )


@router.get("/{id}/show")
def user_show(request: Request, id: int, session: Session = Depends(get_db)):
    user = User.find(id, session)
    user_is_admin = admin_role_enabled(request)
    data = {
        "endpoints": User.endpoints_page(1, 100, user.id, session),
        "validation": {"user": User.valid(), "endpoint": Endpoint.valid()},
        "debug": {"level": application_logger.get_level_str()},
        "admin": user_is_admin,
    }
    return templates.TemplateResponse(
        request, "users/show.html", {"user": user, "data": data}
    )


@router.post("/{id}/displayName")
def user_display_name(
    request: Request,
    id: int,
    name: Annotated[str, Form()],
    session: Session = Depends(get_db),
):
    user = User.find(id, session)
    updated_user, validation = user.update_display_name(name, session)
    use_user = updated_user if updated_user else user
    data = {"validation": {"user": validation}}
    return templates.TemplateResponse(
        request, "users/partials/display_name.html", {"user": use_user, "data": data}
    )


@router.post("/{id}/endpoint")
def create_user_endpoint(
    request: Request,
    id: int,
    name: Annotated[str, Form()],
    url: Annotated[str, Form()],
    session: Session = Depends(get_db),
):
    user = User.find(id, session)
    endpoint, validation = Endpoint.create(name, url, "FHIR", user.id, session)
    data = {
        "endpoints": User.endpoints_page(1, 100, user.id, session),
        "validation": {"endpoint": validation},
    }
    return templates.TemplateResponse(
        request, "users/partials/endpoint.html", {"user": user, "data": data}
    )


@router.delete("/{id}/endpoint/{endpoint_id}")
def delete_user_endpoint(
    request: Request, id: int, endpoint_id: int, session: Session = Depends(get_db)
):
    user = User.find(id, session)
    endpoint = Endpoint.find(endpoint_id, session)
    endpoint.delete(user.id, session)
    data = {
        "endpoints": User.endpoints_page(1, 100, user.id, session),
        "validation": {"endpoint": Endpoint.valid()},
    }
    return templates.TemplateResponse(
        request, "users/partials/endpoint.html", {"user": user, "data": data}
    )
