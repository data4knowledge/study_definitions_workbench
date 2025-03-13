import os
from pathlib import Path
from d4kms_generic import application_logger
from fastapi.templating import Jinja2Templates
from app.utility.template_methods import (
    server_name,
    single_multiple,
    title_page_study_list_headings,
)
from app.dependencies.fhir_version import fhir_version_description
from app.imports.import_manager import ImportManager

full_path = os.path.realpath(__file__)
templates_path = f"{str(Path(full_path).parents[1])}/templates"
templates = Jinja2Templates(directory=templates_path)
application_logger.info(f"Template dir set to '{templates_path}'")

templates.env.globals["server_name"] = server_name
templates.env.globals["single_multiple"] = single_multiple
templates.env.globals["fhir_version_description"] = fhir_version_description
templates.env.globals["title_page_study_list_headings"] = title_page_study_list_headings
templates.env.globals["imports_with_errors"] = ImportManager.imports_with_errors