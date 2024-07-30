from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from d4kms_generic.service_environment import ServiceEnvironment
from d4kms_generic.logger import application_logger

se = ServiceEnvironment()
db_url = se.get("DATABASE_URL")
application_logger.info(f"Database URL '{db_url}'")
engine = create_engine(db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()