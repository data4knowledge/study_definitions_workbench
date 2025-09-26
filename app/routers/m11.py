from fastapi import APIRouter, Form, Depends, Request, status
from sqlalchemy.orm import Session
from app.database.version import Version
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import transmit_role_enabled, user_details
from app.dependencies.templates import templates
from app.utility.template_methods import restructure_study_list
from app.dependencies.fhir_version import fhir_versions
from usdm4_m11.specification import Specification
from usdm4_fhir.status.status import Status
from app.m11.template import parse_elements

router = APIRouter(
    prefix="/m11", tags=["m11"], dependencies=[Depends(protect_endpoint)]
)


@router.get("/specification", dependencies=[Depends(protect_endpoint)])
def m11_spec(
    request: Request,
    session: Session = Depends(get_db),
):
    # data = {}
    user, present_in_db = user_details(request, session)
    data = {
        "fhir": {
            "enabled": transmit_role_enabled(request),
            "versions": fhir_versions(),
        }
    }
    return templates.TemplateResponse(
        request, "m11/specification.html", {"user": user, "data": data}
    )


@router.get("/specification_data", dependencies=[Depends(protect_endpoint)])
def m11_spec_data(
    request: Request,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    data = {}
    specification = Specification()
    data["section_list"] = specification.section_list()
    default_section = specification.default_section
    data["section"] = specification.section(default_section)
    data["element"] = specification.first_element(default_section)
    template = specification.template(default_section)
    data["template"] = parse_elements(
        template, f"/m11/sections/{default_section}/elements"
    )
    return templates.TemplateResponse(
        request, "m11/partials/specification_data.html", {"user": user, "data": data}
    )


@router.get(
    "/sections/{section}/elements/{element}/link", dependencies=[Depends(protect_endpoint)]
)
def element_link(
    request: Request,
    section: str,
    element: str,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    data = {}
    specification = Specification()
    data["element"] = specification.element(section, element)
    data["url"] = f"sections/{section}/elements/{element}/definition"
    return templates.TemplateResponse(
        request, "m11/partials/element_link.html", {"user": user, "data": data}
    )

@router.get(
    "/sections/{section}/elements/{element}/definition", dependencies=[Depends(protect_endpoint)]
)
def element_definition(
    request: Request,
    section: str,
    element: str,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    data = {}
    specification = Specification()
    data["element"] = specification.element(section, element)
    data["mapping"] = specification.mapping(section, element)
    status = Status()
    data["status"] = status.status(element)
    print(f"DATA: {data}")
    return templates.TemplateResponse(
        request, "m11/partials/element_definition.html", {"user": user, "data": data}
    )
