import re
from d4kms_generic.logger import application_logger


class BaseFactory:
    class FHIRError(Exception):
        pass

    def fix_id(self, value: str) -> str:
        result = re.sub('[^0-9a-zA-Z]', '-', value)
        # result = value.replace("_", "-")
        return result.lower()

    def handle_exception(self, e: Exception):
        application_logger.exception(
            f"Exception in FHIR {self.__class__.__name__}, see log for further details",
            e,
        )
        raise BaseFactory.FHIRError
