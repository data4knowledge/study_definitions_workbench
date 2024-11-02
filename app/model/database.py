from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from d4kms_generic.service_environment import ServiceEnvironment
from d4kms_generic.logger import application_logger

se = ServiceEnvironment()
db_path = se.get("DATABASE_PATH")
db_name = se.get("DATABASE_NAME")
db_url = f"sqlite:///{db_path}/{db_name}"
application_logger.info(f"Database URL '{db_url}'")
engine = create_engine(db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#Base = declarative_base()

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()