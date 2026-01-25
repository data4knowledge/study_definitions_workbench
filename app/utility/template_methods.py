import json
from app.configuration.configuration import application_configuration
from d4k_ms_base.logger import application_logger


def server_name(request) -> str:
    application_logger.info(
        f"Base URL used to obtain server name: '{request.base_url}'"
    )
    name = str(request.base_url)
    if "staging" in name:
        return "STAGING"
    elif "training" in name:
        return "TRAINING"
    elif "d4k-sdw" in name:
        return "PRODUCTION"
    elif "localhost" in name:
        return "DEVELOPMENT"
    elif "0.0.0.0" in name:
        return "DEVELOPMENT"
    elif "dnanexus.cloud" in name:
        return "PRISM"
    else:
        return name


def single_multiple() -> str:
    return "SINGLE" if application_configuration.single_user else "MULTIPLE"


def restructure_study_list(data: list[dict]) -> dict:
    result = {}
    first_with_keys = next((i for i, x in enumerate(data) if x is not None), None)
    if first_with_keys is not None:
        for k in data[first_with_keys].keys():
            result[k] = tuple(d[k] for d in data)
    return result

def convert_to_json(data) -> str:
    return json.dumps(data, indent=2)
