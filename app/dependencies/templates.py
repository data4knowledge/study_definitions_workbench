import os
from pathlib import Path
from d4k_ms_base.logger import application_logger
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
templates.env.globals["is_m11_docx_import"] = ImportManager.is_m11_docx_import
templates.env.globals["is_usdm_excel_import"] = ImportManager.is_usdm_excel_import
templates.env.globals["is_fhir_v1_import"] = ImportManager.is_fhir_v1_import
templates.env.globals["is_usdm3_json_import"] = ImportManager.is_usdm3_json_import
templates.env.globals["is_usdm4_json_import"] = ImportManager.is_usdm4_json_import
