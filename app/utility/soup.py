import warnings
from bs4 import BeautifulSoup
from d4k_ms_base.errors_and_logging import application_logger

def get_soup(text: str):
    try:
        with warnings.catch_warnings(record=True) as warning_list:
            result = BeautifulSoup(text, "html.parser")
        if warning_list:
            for item in warning_list:
                application_logger.warning(
                    f"Warning raised within Soup package, processing '{text}'\nMessage returned '{item.message}'"
                )
        return result
    except Exception as e:
        application_logger.exception(f"Parsing '{text}' with soup", e)
        return ""