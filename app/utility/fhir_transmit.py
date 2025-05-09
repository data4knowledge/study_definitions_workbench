import asyncio
import threading
from app.database.database import SessionLocal
from d4k_ms_base.logger import application_logger
from app.model.connection_manager import connection_manager
from app.database.user import User
from app.database.endpoint import Endpoint
from app.database.transmission import Transmission
from app.model.usdm_json import USDMJson
from app.utility.fhir_service import FHIRService
from sqlalchemy.orm import Session


def run_fhir_m11_transmit(
    version_id: int, endpoint_id: int, version: str, user: User
) -> None:
    t = threading.Thread(
        target=asyncio.run,
        args=(fhir_m11_transmit(version_id, endpoint_id, version, user),),
    )
    t.start()


def run_fhir_soa_transmit(
    version_id: int, endpoint_id: int, timeline_id: str, user: User
) -> None:
    t = threading.Thread(
        target=asyncio.run,
        args=(fhir_soa_transmit(version_id, endpoint_id, timeline_id, user),),
    )
    t.start()


async def fhir_m11_transmit(
    version_id: int, endpoint_id: int, version: str, user: User
) -> None:
    session = SessionLocal()
    usdm = USDMJson(version_id, session)
    details = usdm.study_version()
    application_logger.info(f"M11 FHIR tx, version: {version}")
    data = usdm.fhir_data(version)
    await fhir_transmit("M11", version_id, endpoint_id, data, details, user, session)


async def fhir_soa_transmit(
    version_id: int, endpoint_id: int, timeline_id: str, user: User
) -> None:
    session = SessionLocal()
    usdm = USDMJson(version_id, session)
    details = usdm.study_version()
    data = usdm.fhir_soa_data(timeline_id)
    await fhir_transmit("SoA", version_id, endpoint_id, data, details, user, session)


async def fhir_transmit(
    type: str,
    version_id: int,
    endpoint_id: int,
    data: str,
    details: dict,
    user: User,
    session: Session,
) -> None:
    ERROR_LEN = 100
    try:
        # session = SessionLocal()
        application_logger.info(
            f"Sending FHIR message from version id '{version_id}' to endpoint id '{endpoint_id}'"
        )
        # usdm = USDMJson(version_id, session)
        # details = usdm.study_version()
        # # print(f"DETAILS: {details}")
        tx = Transmission.create(
            version=version_id,
            study=details["titles"]["Official Study Title"],
            status="Preparing",
            user_id=user.id,
            session=session,
        )
        # data = usdm.fhir_data(version)
        endpoint = Endpoint.find(endpoint_id, session)
        application_logger.info(f"Sending FHIR message, endpoint '{endpoint}'")
        server = FHIRService(endpoint.endpoint)
        response = await server.post("Bundle", data, 30.0)
        if response["success"]:
            message = f"Succesful transmission of FHIR {type} message: {response['data']['id']}"
        else:
            error_text = (
                f"{response['message'][0:ERROR_LEN]} ..."
                if len(response["message"]) > ERROR_LEN
                else response["message"]
            )
            message = f"Unsuccesful transmission of FHIR {type} message: {error_text}"
        tx.update_status(status=message, session=session)
        application_logger.info(message)
        session.close()
        if response["success"]:
            await connection_manager.success(message, str(user.id))
        else:
            await connection_manager.error(message, str(user.id))
    except Exception as e:
        application_logger.exception(
            f"Exception transmititng FHIR {type} message from version '{version_id}' to endpoint: {endpoint_id}",
            e,
        )
        session.close()
        await connection_manager.error(
            f"Error encountered transmititng FHIR {type} message from version '{version_id}' to endpoint: '{endpoint_id}'",
            str(user.id),
        )
