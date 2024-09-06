from d4kms_generic import application_logger
from app.utility.background import process_excel, process_word, process_fhir_v1

from app.model.user import User
from app.model.endpoint import Endpoint
from sqlalchemy.orm import Session
from app.utility.template_methods import server_environment
from app.model.usdm_json import USDMJson
from app.model.database_manager import DatabaseManager as DBM
from app.utility.fhir_service import FHIRService

async def transmit(version_id: int, endpoint_id: int, user: User, session: Session):
  try:
    application_logger.info(f"Sending FHIR message from version id '{version_id}' to endpoint id '{endpoint_id}'")
    usdm = USDMJson(version_id, session)
    data = usdm.fhir_data()
    endpoint = Endpoint.find(endpoint_id, session)
    application_logger.info(f"Sending FHIR message, endpoint '{endpoint}'")
    server = FHIRService(endpoint.endpoint)
    response = await server.post('Bundle', data, 20.0)
    application_logger.info(f"Sending FHIR message response: {response}")
  except Exception as e:
    application_logger.exception("Exception transmititng FHIR message from version '{version_id}' to endpoint: {endpoint_id}", e)

