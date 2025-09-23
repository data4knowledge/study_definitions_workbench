from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import transmit_role_enabled, user_details
from app.dependencies.templates import templates
from app.database.transmission import Transmission
from app.utility.fhir_uuid import extract_uuid
from d4k_ms_ui.pagination import Pagination

router = APIRouter(
    prefix="/transmissions",
    tags=["transmissions"],
    dependencies=[Depends(protect_endpoint)],
)


@router.get("/status")
async def import_status(
    request: Request,
    page: int,
    size: int,
    filter: str = "",
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    if transmit_role_enabled(request):
        data = {"page": page, "size": size, "filter": filter}
        return templates.TemplateResponse(
            request, "transmissions/status.html", {"user": user, "data": data}
        )
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {
                "user": user,
                "data": {"error": "User is not authorised to transmit FHIR messages."},
            },
        )


@router.get("/status/data")
async def import_status(
    request: Request,
    page: int,
    size: int,
    filter: str = "",
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    if transmit_role_enabled(request):
        data = Transmission.page(page, size, user.id, session)
        for item in data["items"]:
            item["uuid"] = None
            if item["status"].startswith("Succesful transmission"):
                uuid = extract_uuid(item["status"])
                if uuid:
                    item["uuid"] = uuid
        pagination = Pagination(data, "/transmissions/status/data")
        return templates.TemplateResponse(
            request,
            "transmissions/partials/status.html",
            {"user": user, "pagination": pagination, "data": data},
        )
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {
                "user": user,
                "data": {"error": "User is not authorised to transmit FHIR messages."},
            },
        )
