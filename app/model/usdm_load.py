from pydantic import ValidationError
from simple_error_log import Errors
from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper

from app.model.exceptions import USDMLoadException


def load_usdm4(usdm4: USDM4, data: dict) -> Wrapper:
    """Load a USDM v4 dict into the usdm4 model, raising
    ``USDMLoadException`` when it does not validate.

    ``USDM4.loadd`` swallows the validation error and returns ``None``;
    a caller that does not check that crashes later on a ``None``
    dereference far from the cause (issue 79)."""
    wrapper = usdm4.loadd(data, Errors())
    if wrapper is None:
        raise USDMLoadException(validation_problems(data))
    return wrapper


def validation_problems(data: dict) -> list[str]:
    """One line per model validation error: ``<field path>: <reason>``.

    Re-validates to get pydantic's structured errors, since ``loadd``
    only records them as text with a traceback attached. Only runs on
    the failure path."""
    try:
        Wrapper.model_validate(data)
    except ValidationError as e:
        return [
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in e.errors()
        ]
    return ["The file could not be loaded as USDM v4"]
