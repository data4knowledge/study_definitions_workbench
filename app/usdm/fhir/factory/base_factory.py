import re
from d4k_ms_base.logger import application_logger


class BaseFactory:
    class FHIRError(Exception):
        pass

    def handle_exception(self, e: Exception):
        application_logger.exception(
            f"Exception in FHIR {self.__class__.__name__}, see log for further details",
            e,
        )
        raise BaseFactory.FHIRError

    @staticmethod
    def fix_id(value: str) -> str:
        result = re.sub("[^0-9a-zA-Z]", "-", value)
        result = "-".join([s for s in result.split("-") if s != ""])
        return result.lower()
