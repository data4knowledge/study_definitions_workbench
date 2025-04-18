from usdm_model.code import Code
from d4k_ms_base.logger import application_logger


class CDISCFHIR:
    @classmethod
    def from_c201264(cls, code: Code) -> str:
        """Converts a CDISC code for reletive timing to the equivalent FHIR value"""
        map = {"After": "after", "Before": "before", "Fixed Reference": "concurrent"}
        result = map.get(code.decode, "concurrent")
        application_logger.info(f"CDISC FHIR: {code.decode} -> {result}")
        return result
