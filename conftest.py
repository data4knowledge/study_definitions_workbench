import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from d4kms_generic.service_environment import ServiceEnvironment
from app.model import database_tables

@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
  set_test()
  yield
  clear_test()

@pytest.fixture
def db():
  se = ServiceEnvironment()
  db_path = se.get("DATABASE_PATH")
  db_name = se.get("DATABASE_NAME")
  db_url = f"sqlite:///{db_path}/{db_name}"
  engine = create_engine(db_url, connect_args={"check_same_thread": False})
  TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  database_tables.Base.metadata.create_all(bind=engine)
  return TestSession()

def set_test():
  os.environ["PYTHON_ENVIRONMENT"] = "test"

def clear_test():
  os.environ["PYTHON_ENVIRONMENT"] = "development"
