import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
  os.environ["PYTHON_ENVIRONMENT"] = "test"
  yield
  os.environ["PYTHON_ENVIRONMENT"] = "development"
