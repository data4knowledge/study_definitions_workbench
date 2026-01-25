import os
from pathlib import Path
from d4k_ms_base.logger import application_logger
from fastapi.templating import Jinja2Templates
from app.utility.template_methods import (
    server_name,
    single_multiple,
    convert_to_json,
)
from app.dependencies.fhir_version import (
    fhir_version_description,
    fhir_version_export,
    fhir_version_import,
    fhir_version_transmit,
)
from app.imports.import_manager import ImportManager

full_path = os.path.realpath(__file__)
templates_path = f"{str(Path(full_path).parents[1])}/templates"
templates = Jinja2Templates(directory=templates_path)
application_logger.info(f"Template dir set to '{templates_path}'")

templates.env.globals["server_name"] = server_name
templates.env.globals["single_multiple"] = single_multiple
templates.env.globals["convert_to_json"] = convert_to_json
templates.env.globals["fhir_version_description"] = fhir_version_description
templates.env.globals["fhir_version_import"] = fhir_version_import
templates.env.globals["fhir_version_export"] = fhir_version_export
templates.env.globals["fhir_version_transmit"] = fhir_version_transmit
templates.env.globals["imports_with_errors"] = ImportManager.imports_with_errors
templates.env.globals["is_m11_docx_import"] = ImportManager.is_m11_docx_import
templates.env.globals["is_cpt_docx_import"] = ImportManager.is_cpt_docx_import
templates.env.globals["is_legacy_pdf_import"] = ImportManager.is_legacy_pdf_import
templates.env.globals["is_usdm_excel_import"] = ImportManager.is_usdm_excel_import
templates.env.globals["is_fhir_prism2_import"] = ImportManager.is_fhir_prism2_import
templates.env.globals["is_fhir_prism3_import"] = ImportManager.is_fhir_prism3_import
templates.env.globals["is_usdm3_json_import"] = ImportManager.is_usdm3_json_import
templates.env.globals["is_usdm4_json_import"] = ImportManager.is_usdm4_json_import
