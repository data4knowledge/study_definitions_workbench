import asyncio
import threading
from app.model.database import SessionLocal
from d4kms_generic import application_logger
from app.model.connection_manager import connection_manager
from app.model.user import User
from app.model.endpoint import Endpoint
from sqlalchemy.orm import Session
from app.model.transmission import Transmission
from app.model.usdm_json import USDMJson
from app.model.database_manager import DatabaseManager as DBM
from app.utility.fhir_service import FHIRService

def run_fhir_transmit(version_id: int, endpoint_id: int, version: str, user: User) -> None:
  t = threading.Thread(target=asyncio.run, args=(fhir_transmit(version_id, endpoint_id, version, user),))
  t.start()

async def fhir_transmit(version_id: int, endpoint_id: int, version: str, user: User):
  ERROR_LEN = 100
  try:
    session = SessionLocal()
    application_logger.info(f"Sending FHIR message from version id '{version_id}' to endpoint id '{endpoint_id}'")
    usdm = USDMJson(version_id, session)
    details = usdm.study_version()
    #print(f"DETAILS: {details}")
    tx = Transmission.create(version=version_id, study=details['titles']['Official Study Title'], status='Preparing', user_id=user.id, session=session)
    data = usdm.fhir_data(version)
    endpoint = Endpoint.find(endpoint_id, session)
    application_logger.info(f"Sending FHIR message, endpoint '{endpoint}'")
    server = FHIRService(endpoint.endpoint)
    response = await server.post('Bundle', data, 30.0)
    if response['success']:
      message = f"Succesful transmission of FHIR message: {response['data']['id']}"
    else:
      error_text = f"{response['message'][0:ERROR_LEN]} ..." if len(response['message']) > ERROR_LEN else response['message']
      message = f"Unsuccesful transmission of FHIR message: {error_text}"
    tx.update_status(status=message, session=session)
    application_logger.info(message)
    session.close()
    if response['success']:
      await connection_manager.success(message, str(user.id))
    else:
      await connection_manager.error(message, str(user.id))      
  except Exception as e:
    application_logger.exception("Exception transmititng FHIR message from version '{version_id}' to endpoint: {endpoint_id}", e)
    session.close()
    await connection_manager.error(f"Error encountered transmititng FHIR message from version '{version_id}' to endpoint: '{endpoint_id}'", str(user.id))

