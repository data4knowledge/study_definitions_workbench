from d4kms_generic.logger import application_logger


class BaseFactory:
    class FHIRError(Exception):
        pass

    def fix_id(self, value: str) -> str:
        return value.replace("_", "-")

    def handle_exception(self, e: Exception):
        application_logger.exception(
            f"Exception in FHIR {self.__class__.__name__}, see log for further details",
            e,
        )
        raise BaseFactory.FHIRError
