from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from d4kms_generic.logger import application_logger
from app.configuration.configuration import application_configuration

db_path = application_configuration.database_path
db_name = application_configuration.database_name
db_url = f"sqlite:///{db_path}/{db_name}"
application_logger.info(f"Database URL '{db_url}'")
engine = create_engine(db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()