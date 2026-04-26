import json
from d4k_ms_base.logger import application_logger
from usdm_db import USDMDb
from usdm4_protocol.m11 import USDM4M11
from usdm4_protocol.cpt import USDM4CPT

# from usdm4_legacy import USDM4Legacy
from usdm4_fhir import M11
from usdm4.api.wrapper import Wrapper
from usdm4.api.study_version import StudyVersion
from usdm4.api.identifier import StudyIdentifier
from usdm4_protocol.validation.m11 import M11Validator
from simple_error_log import Errors as M11Errors
from app.model.object_path import ObjectPath
from app.model.file_handling.data_files import DataFiles
from app.utility.finding_projections import project_m11_result
from app.configuration.configuration import application_configuration
from usdm4 import USDM4
from usdm3 import USDM3, RulesValidationResults
import simple_error_log as sel


def _usdm4() -> USDM4:
    """Build a USDM4 facade wired to the configured CORE cache path.

    The cache path is only read by the CORE validation subsystem, but we
    pass it on every instantiation so the pattern stays uniform — if a
    future caller adds ``validate_core`` to an import processor, the
    cache is already configured correctly.
    """
    return USDM4(cache_dir=application_configuration.cdisc_core_cache_path or None)


class ImportProcessorBase:
    def __init__(self, type: str, uuid: str, full_path: str) -> None:
        self.usdm = None
        self.errors = None
        self.study_parameters = None
        self.fatal_error = None
        self.success = True
        self.extra = self._blank_extra()
        self.type = type
        self.uuid = uuid
        self.full_path = full_path

    async def process(self) -> bool:
        return False

    def _study_parameters(self) -> dict | None:
        try:
            data = json.loads(self.usdm)
            db = _usdm4()
            wrapper: Wrapper = db.from_json(data)
            object_path = ObjectPath(wrapper)
            version: StudyVersion = wrapper.study.first_version()
            # print(f"STUDY VERSION: {type(version)}")
            nct: StudyIdentifier = version.nct_identifier()
            return {
                "name": f"{self._get_parameter(object_path, 'study/name')}-{self.type}",
                "phase": version.phases(),
                "full_title": version.official_title_text(),
                "sponsor_identifier": version.sponsor_identifier_text(),
                "nct_identifier": nct.text if nct else "",
                "sponsor": version.sponsor_label_name(),
            }
        except Exception as e:
            application_logger.exception(
                "Exception raised extracting study parameters", e
            )
            return None

    def _get_parameter(self, object_path: ObjectPath, path: str) -> str:
        value = object_path.get(path)
        return value if value else ""

    def _fallback_parameters(self) -> dict:
        """Synthesize a minimal study-parameters dict for files where
        the real fields can't be extracted.

        Used when a USDM file is structurally non-conforming enough that
        ``_study_parameters`` raises while reaching for ``first_version``,
        ``official_title_text``, etc. Lets the import still land — the
        user can inspect the file and the persisted findings from the
        study view rather than being shut out at the door.

        ``name`` is left empty on purpose so ``Study.study_and_version``
        falls through to ``_set_study_name`` and synthesizes one from
        the file_import (matching how malformed files were named even
        before this fallback existed)."""
        return {
            "name": "",
            "phase": "",
            "full_title": "",
            "sponsor_identifier": "",
            "nct_identifier": "",
            "sponsor": "",
        }

    def _blank_extra(self):
        return {
            "amendment": {
                "amendment_details": "",
                "robustness_impact": False,
                "robustness_impact_reason": "",
                "safety_impact": False,
                "safety_impact_reason": "",
            },
            "miscellaneous": {
                "medical_expert_contact": "",
                "sae_reporting_method": "",
                "sponsor_signatory": "",
            },
            "title_page": {
                "amendment_details": "",
                "amendment_identifier": "",
                "amendment_scope": "",
                "compound_codes": "",
                "compound_names": "",
                "manufacturer_name_and_address": "",
                "medical_expert_contact": "",
                "original_protocol": "",
                "regulatory_agency_identifiers": "",
                "sae_reporting_method": "",
                "sponsor_approval_date": "",
                "sponsor_confidentiality": "",
                "sponsor_name_and_address": "",
                "sponsor_signatory": "",
            },
        }


class ImportExcel(ImportProcessorBase):
    async def process(self) -> bool:
        db = USDMDb()
        self.errors = db.from_excel(self.full_path)
        self.usdm = db.to_json()
        self.study_parameters = self._study_parameters()
        return True


class ImportM11(ImportProcessorBase):
    async def process(self) -> bool:
        # Initial M11 specification validation runs against the raw DOCX
        # via the standalone :class:`M11Validator` (no USDM translation
        # step). Findings are persisted as the ``m11_validation`` media
        # type so the study view can surface them later; failures here
        # must NOT stop the import — the validator is advisory, not a
        # gate. The findings are also kept on ``self.m11_validation``
        # so the end-of-import flow can surface them directly.
        self.m11_validation: list[dict] = []
        try:
            validator_errors = M11Errors()
            results = M11Validator(self.full_path, validator_errors).validate()
            self.m11_validation = project_m11_result(results)
            DataFiles(self.uuid).save(
                "m11_validation", json.dumps(self.m11_validation)
            )
        except Exception as e:
            application_logger.exception(
                "Exception raised during M11 validation step", e
            )

        importer = USDM4M11()
        wrapper: Wrapper = importer.from_docx(self.full_path, use_ai=True)
        application_logger.info(importer.errors.dump(sel.Errors.DEBUG))
        if wrapper:
            self.usdm = wrapper.to_json()
            self.extra = self._blank_extra()
            self.study_parameters = self._study_parameters()
        self.errors = importer.errors.to_dict(sel.Errors.INFO)
        return True


class ImportCPT(ImportProcessorBase):
    async def process(self) -> bool:
        importer = USDM4CPT()
        wrapper: Wrapper = importer.from_docx(self.full_path)
        application_logger.info(importer.errors.dump(sel.Errors.DEBUG))
        if wrapper:
            self.usdm = wrapper.to_json()
            self.extra = importer.extra
            self.study_parameters = self._study_parameters()
        self.errors = importer.errors.to_dict(sel.Errors.INFO)
        return True


class ImportLegacy(ImportProcessorBase):
    async def process(self) -> bool:
        application_logger.info("Legacy import currently diabled")
        # importer = USDM4Legacy()
        # wrapper: Wrapper = importer.from_pdf(self.full_path)
        # application_logger.info(importer.errors.dump(sel.Errors.DEBUG))
        # if wrapper:
        #     self.usdm = wrapper.to_json()
        #     self.extra = importer.extra
        #     self.study_parameters = self._study_parameters()
        # self.errors = importer.errors.to_dict(sel.Errors.INFO)
        return True


class ImportFhirPRISM2(ImportProcessorBase):
    async def process(self) -> bool:
        importer = M11()
        wrapper: Wrapper = await importer.from_message(self.full_path, M11.PRISM2)
        application_logger.info(importer.errors.dump(sel.Errors.DEBUG))
        if wrapper:
            self.usdm = wrapper.to_json()
            self.extra = importer.extra
            self.study_parameters = self._study_parameters()
            print(f"STUDY PARAMS: {self.study_parameters}")
            self.errors = importer.errors.to_dict(sel.Errors.INFO)
            self.success = True
        else:
            self.success = False
            self.errors = importer.errors.to_dict(sel.Errors.INFO)
            self.fatal_error = "FHIR (PRISM2) import failed, check the error file"
        return self.success


class ImportFhirPRISM3(ImportProcessorBase):
    async def process(self) -> bool:
        importer = M11()
        wrapper: Wrapper = await importer.from_message(self.full_path, M11.PRISM3)
        application_logger.info(importer.errors.dump(sel.Errors.DEBUG))
        if wrapper:
            self.usdm = wrapper.to_json()
            self.extra = self._blank_extra()
            self.study_parameters = self._study_parameters()
            self.errors = importer.errors.to_dict(sel.Errors.INFO)
            self.success = True
        else:
            self.success = False
            self.errors = importer.errors.to_dict(sel.Errors.INFO)
            self.fatal_error = "FHIR (PRISM3) import failed, check the error file"
        return self.success


class ImportUSDM3(ImportProcessorBase):
    """Import a USDM v3 JSON file.

    Runs the v3 rules library for diagnostics, converts to v4, runs the
    v4 rules library on the converted file, then extracts study
    parameters (falling back to a minimal placeholder dict if the file
    is non-conforming enough that the parameter accessors raise).
    Validation findings are persisted to the errors file (via
    :class:`ImportManager`) but the import always lands — findings are
    advisory and the user reviews them via the study view.

    The only path that still surfaces a fatal error is a v3 → v4
    conversion crash: without a v4 file we have nothing to save.
    """

    async def process(self) -> bool:
        data_files = DataFiles(self.uuid)
        full_path, filename, exists = data_files.path("usdm")
        usdm3 = USDM3()
        # Run v3 validation for the record. Findings are kept in scope
        # so the v3-side errors surface if conversion crashes before we
        # have a v4 file to validate against.
        v3_results: RulesValidationResults = usdm3.validate(full_path)
        try:
            usdm4 = _usdm4()
            wrapper = usdm4.convert(full_path)
            self.usdm = wrapper.to_json()
            data_files.save("usdm", self.usdm)  # Save USDM in new version
            full_path, filename, exists = data_files.path("usdm")
            v4_results: RulesValidationResults = usdm4.validate(full_path)
            # The v4 errors are the more actionable diagnostic — the
            # converted file is what's stored, so its rule output is
            # what users will be remediating against.
            self.errors = v4_results.to_dict()
            # Parameter extraction is best-effort. Files with rule
            # violations may also have structural issues that make the
            # high-level accessors (``first_version``, ``phases``, ...)
            # raise; the fallback gives us a placeholder so the study
            # still lands and can be reviewed.
            self.study_parameters = (
                self._study_parameters() or self._fallback_parameters()
            )
        except Exception as e:
            # v3 → v4 conversion crashed. Without a v4 file we have
            # nothing to anchor a study record to, so the import does
            # have to stop here. Persist the v3 findings as the
            # diagnostic the user can act on.
            application_logger.exception("USDM v3 → v4 conversion failed", e)
            self.errors = v3_results.to_dict()
            self.success = False
            self.fatal_error = (
                "USDM v3 → v4 conversion failed; cannot import this file. "
                "Check the file using the validate functionality."
            )
        application_logger.info(self.errors)
        return self.success


class ImportUSDM4(ImportProcessorBase):
    """Import a USDM v4 JSON file.

    Runs the v4 rules library for diagnostics and persists the findings
    to the errors file via :class:`ImportManager`. The import always
    succeeds when the file reaches this processor — validation findings
    are advisory, and even a parameter-extraction failure (caused by a
    structurally non-conforming file) falls back to a placeholder dict
    rather than blocking. The user reviews the imported study and the
    persisted findings to figure out what's wrong.
    """

    async def process(self) -> bool:
        data_files = DataFiles(self.uuid)
        full_path, filename, exists = data_files.path("usdm")
        self.usdm = data_files.read("usdm")
        usdm4 = _usdm4()
        results: RulesValidationResults = usdm4.validate(full_path)
        self.errors = results.to_dict()
        # Best-effort parameter extraction; if the file is malformed
        # enough that the wrapper can't surface a sponsor / title /
        # phase, we still land the study with placeholder values so
        # the user can open it and see the persisted findings.
        self.study_parameters = (
            self._study_parameters() or self._fallback_parameters()
        )
        return self.success
