from fastapi import APIRouter, Form, Depends, Request, status
from sqlalchemy.orm import Session
from app.database.version import Version
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import transmit_role_enabled, user_details
from app.dependencies.templates import templates
from app.utility.template_methods import restructure_study_list
from app.dependencies.fhir_version import fhir_versions
#from usdm4_m11.specification import Specification
from app.m11.template import parse_elements

router = APIRouter(
    prefix="/m11", tags=["m11"], dependencies=[Depends(protect_endpoint)]
)


@router.get("/specification", dependencies=[Depends(protect_endpoint)])
def study_select(
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
def study_select(
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
    data["template"] = parse_elements(template, f"/m11/sections/{default_section}/elements")
    print(f"TEMPLATE: {data["template"]}")
    return templates.TemplateResponse(
        request, "m11/partials/specification_data.html", {"user": user, "data": data}
    )

@router.get("/sections/{section}/elements/{element}", dependencies=[Depends(protect_endpoint)])
def study_select(
    request: Request,
    section: str,
    element: str,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    data = {}
    specification = Specification()
    data["element"] = specification.element(section, element)
    return templates.TemplateResponse(
        request, "m11/partials/element_data.html", {"user": user, "data": data}
    )

# -----------------------------------------------------

import os
from simple_error_log import Errors
from simple_error_log.error_location import KlassMethodLocation

import os
import yaml
import pathlib

@staticmethod
def read_yaml(full_path: str) -> dict:
    with open(full_path, "r") as f:
        result = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
    return result

@staticmethod
def read_html(full_path: str) -> str:
    with open(full_path, "r") as f:
        result = f.read()
        f.close()
    return result

@staticmethod
def root() -> str:
    return "/Users/daveih/Documents/python/usdm4_m11/src/usdm4_m11"
    # path = pathlib.Path(__file__).parent.resolve()
    # print(f"ROOT PATH: {type(path)} {path}")
    # return path

@staticmethod
def sections_file() -> str:
    return os.path.join(root(), "data/specification/sections.yaml")

class Specification():
    MODULE = "usdm4_m11.specification.Specification"

    def __init__(self):
        self._root = root()
        self._errors = Errors()

    @property
    def default_section(self):
        return "title_page"
    
    def section_list(self) -> list[str] | None:
        return Sections(self._root, self._errors).list()

    def section(self, section: str) -> str | None:
        return Section(section, self._root, self._errors).content(section)

    def first_element(self, section: str) -> str | None:
        section: Section = Section(section, self._root, self._errors)
        return section.first_element()
    
    def element(self, section: str, element: str) -> str | None:
        section: Section = Section(section, self._root, self._errors)
        return section.element(element)

    def template(self, section: str) -> str:
        section: Section = Section(section, self._root, self._errors)
        return section.template()

class Sections():
    MODULE = "usdm4_m11.specification.sections.Sections"

    def __init__(self, root: str, errors: Errors):
        self._root = root
        self._errors = errors
   
    def list(self) -> list[str] | None:
        results = []
        sections = read_yaml(sections_file())
        section: dict
        for section, section_data in sections.items():
            print(f"SECTION: {section}, {section_data}")
            results.append({
                "section_number": section_data["number"] if section_data["number"] else "",
                "section_title": section_data["title"],
                "name": section
            })
        return list[sections.keys()]

class Section():
    MODULE = "usdm4_m11.specification.section.Section"

    def __init__(self, section: str, root: str, errors: Errors):
        self._section = section
        self._root = root
        self._errors = errors
        self._sections = None

    def content(self, section: str) -> str | None:
        self._read_sections()
        return self._sections[section] if section in self._sections else None

    def elements(self) -> list[dict]:
        self._read_sections()
        return self._read_elements()

    def element(self, name: str) -> dict:
        self._read_sections()
        elements = self._read_elements()
        return elements[name]

    def first_element(self) -> dict:
        self._read_sections()
        elements = self._read_elements()
        print(f"ELEMENTS: {elements.keys()}")
        element = next((v for k, v in elements.items() if v["ordinal"] == 1), None)
        return element

    def template(self) -> str:
        self._read_sections()
        result = self._read_template()
        return result

    def _read_sections(self):
        if not self._sections:
            print("READING SECTIONS")
            self._sections = read_yaml(sections_file())
        return self._sections

    def _read_elements(self):
        filepath = self._elements_file()
        return read_yaml(filepath)

    def _read_template(self):
        filepath = self._template_file()
        return read_html(filepath)

    def _elements_file(self) -> str:
        filename = self._sections[self._section]["elements"]
        return os.path.join(self._root, filename)
    
    def _template_file(self) -> str:
        print(f"TEMPLATE FILE: {self._section}")
        filename = self._sections[self._section]["template"]
        return os.path.join(self._root, filename)
    
