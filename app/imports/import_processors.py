import json
from d4kms_generic import application_logger
from usdm_db import USDMDb
from app.model.m11_protocol.m11_protocol import M11Protocol
from app.usdm.fhir.from_fhir_v1 import FromFHIRV1
from app import VERSION, SYSTEM_NAME
from app.model.object_path import ObjectPath
from app.model.file_handling.data_files import DataFiles
from usdm4 import USDM4
from usdm3 import USDM3, RulesValidationResults


class ImportProcessorBase:
    def __init__(self, type: str, uuid: str, full_path: str) -> None:
        self.usdm = None
        self.errors = None
        self.study_paramters = None
        self.fatal_error = None
        self.success = True
        self.extra = self._blank_extra()
        self.type = type
        self.uuid = uuid
        self.full_path = full_path

    async def process(self) -> None:
        pass

    def _study_parameters(self) -> dict:
        try:
            data = json.loads(self.usdm)
            db = USDMDb()
            db.from_json(data)
            object_path = ObjectPath(db.wrapper())
            version = db.wrapper().study.first_version()
            return {
                "name": f"{self._get_parameter(object_path, 'study/name')}-{self.type}",
                "phase": self._get_parameter(
                    object_path, "study/versions[0]/studyPhase/standardCode/decode"
                ),
                "full_title": version.official_title_text(),
                "sponsor_identifier": version.sponsor_identifier_text(),
                "nct_identifier": version.nct_identifier(),
                "sponsor": version.sponsor_name(),
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
        # self.file_import.update_status("Saving", self.session)
        self.usdm = db.to_json()
        self.study_parameters = self._study_parameters()
        return True


class ImportWord(ImportProcessorBase):
    async def process(self) -> None:
        m11 = M11Protocol(self.full_path, SYSTEM_NAME, VERSION)
        await m11.process()
        self.usdm = m11.to_usdm()
        self.extra = m11.extra()
        self.study_parameters = self._study_parameters()
        return True


class ImportFhirV1(ImportProcessorBase):
    async def process(self) -> None:
        fhir = FromFHIRV1(self.uuid)
        self.usdm = await fhir.to_usdm()
        self.study_parameters = self._study_parameters()
        return True


class ImportUSDM3(ImportProcessorBase):
    async def process(self) -> None:
        data_files = DataFiles(self.uuid)
        full_path, filename, exists = data_files.path("usdm")
        usdm3 = USDM3()
        results: RulesValidationResults = usdm3.validate(full_path)
        if results.passed_or_not_implemented():
            usdm4 = USDM4()
            wrapper = usdm4.convert(full_path)
            self.usdm = wrapper.to_json()
            data_files.save("usdm", self.usdm)  # Save USDM in new version
            full_path, filename, exists = data_files.path("usdm")
            results: RulesValidationResults = usdm4.validate(full_path)
            self.errors = results.to_dict()
            if results.passed_or_not_implemented():
                self.study_parameters = self._study_parameters()
            else:
                self.success = False
                self.fatal_error = "USDM v4 validation failed. Check the file using the validate functionality"
        else:
            self.errors = results.to_dict()
            self.success = False
            self.fatal_error = "USDM v3 validation failed. Check the file using the validate functionality"
        return self.success


class ImportUSDM4(ImportProcessorBase):
    async def process(self) -> None:
        data_files = DataFiles(self.uuid)
        full_path, filename, exists = data_files.path("usdm")
        self.usdm = data_files.read("usdm")
        usdm4 = USDM4()
        results: RulesValidationResults = usdm4.validate(full_path)
        self.errors = results.to_dict()
        # data_files.save("errors", self.errors)
        if results.passed_or_not_implemented():
            self.study_parameters = self._study_parameters()
        else:
            self.success = False
            self.fatal_error = "USDM v4 validation failed. Check the file using the validate functionality"
        return self.success
