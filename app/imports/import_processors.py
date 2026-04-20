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
    async def process(self) -> bool:
        data_files = DataFiles(self.uuid)
        full_path, filename, exists = data_files.path("usdm")
        usdm3 = USDM3()
        results: RulesValidationResults = usdm3.validate(full_path)
        if results.passed_or_not_implemented():
            usdm4 = _usdm4()
            wrapper = usdm4.convert(full_path)
            self.usdm = wrapper.to_json()
            data_files.save("usdm", self.usdm)  # Save USDM in new version
            full_path, filename, exists = data_files.path("usdm")
            results: RulesValidationResults = usdm4.validate(full_path)
            self.errors = results.to_dict()
            if results.passed_or_not_implemented():
                self.study_parameters = self._study_parameters()
            else:  # pragma: no cover
                self.success = False
                self.fatal_error = "USDM v4 validation failed. Check the file using the validate functionality"
        else:
            self.errors = results.to_dict()
            self.success = False
            self.fatal_error = "USDM v3 validation failed. Check the file using the validate functionality"
        application_logger.info(self.errors)
        return self.success


class ImportUSDM4(ImportProcessorBase):
    async def process(self) -> bool:
        data_files = DataFiles(self.uuid)
        full_path, filename, exists = data_files.path("usdm")
        self.usdm = data_files.read("usdm")
        usdm4 = _usdm4()
        results: RulesValidationResults = usdm4.validate(full_path)
        # application_logger.info(results.to_dict(sel.Errors.DEBUG))
        self.errors = results.to_dict()
        # data_files.save("errors", self.errors)
        if results.passed_or_not_implemented():
            self.study_parameters = self._study_parameters()
        else:
            self.success = False
            self.fatal_error = "USDM v4 validation failed. Check the file using the validate functionality"
        return self.success
