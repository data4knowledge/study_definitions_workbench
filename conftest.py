import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import database_tables


def set_test():
    os.environ["PYTHON_ENVIRONMENT"] = "test"


def clear_test():
    os.environ["PYTHON_ENVIRONMENT"] = "development"


set_test()


@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
    set_test()
    load_dotenv(".test_env", override=True)
    yield
    clear_test()


@pytest.fixture
def db():
    db_path = os.environ["DATABASE_PATH"]
    db_name = os.environ["DATABASE_NAME"]
    db_url = f"sqlite:///{db_path}/{db_name}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database_tables.Base.metadata.create_all(bind=engine)
    return TestSession()


def pytest_configure(config):
    config.addinivalue_line("markers", "playwright:  marks tests as playwright tests")
