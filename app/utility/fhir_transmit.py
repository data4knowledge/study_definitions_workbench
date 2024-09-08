import asyncio
from d4kms_generic import application_logger
from app.model.connection_manager import connection_manager
from app.model.user import User
from app.model.endpoint import Endpoint
from sqlalchemy.orm import Session
from app.model.transmission import Transmission
from app.model.usdm_json import USDMJson
from app.model.database_manager import DatabaseManager as DBM
from app.utility.fhir_service import FHIRService

async def fhir_transmit(version_id: int, endpoint_id: int, version: str, user: User, session: Session):
  try:
    application_logger.info(f"Sending FHIR message from version id '{version_id}' to endpoint id '{endpoint_id}'")
    usdm = USDMJson(version_id, session)
    details = usdm.study_version()
    print(f"DETAILS: {details}")
    tx = Transmission.create(version=version_id, study=details['titles']['Official Study Title'], status='Preparing', user_id=user.id, session=session)
    data = usdm.fhir_data(version)
    endpoint = Endpoint.find(endpoint_id, session)
    application_logger.info(f"Sending FHIR message, endpoint '{endpoint}'")
    server = FHIRService(endpoint.endpoint)
    response = await server.post('Bundle', data, 20.0)
    tx.update_status(status=f'Complete. {response}', session=session)
    application_logger.info(f"Sending FHIR message response: {response}")
    await connection_manager.success(f"Sending of FHIR message completed: {response}", str(user.id))
  except Exception as e:
    application_logger.exception("Exception transmititng FHIR message from version '{version_id}' to endpoint: {endpoint_id}", e)
    await asyncio.sleep(1) # Need something just in case background task does not block
    await connection_manager.error(f"Error encountered transmititng FHIR message from version '{version_id}' to endpoint: {endpoint_id}", str(user.id))

