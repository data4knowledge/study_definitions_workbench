"""Push a study version's USDM v4 JSON to the d4k backbone.

Mirrors the FHIR transmit pattern (``fhir_transmit.py``): the HTTP call
runs on a background thread, progress is recorded in the Transmission
audit table, and the outcome is pushed to the user over the WebSocket
connection manager.

The backbone endpoint is ``POST {BACKBONE_URL}/v1/studies`` taking a
multipart upload with a single ``file`` field carrying the USDM v4 JSON
(the ``usdm.json`` DataFiles artefact for the version). Responses:
200/201 success with ``{slug, study_id, graph_uri, triple_count}``,
409 when that protocol version is already loaded, 400 for invalid JSON,
422 when no slug can be derived from the study identifiers.

Configuration: ``BACKBONE_URL`` enables the feature (menu item hidden and
route refuses when unset); ``BACKBONE_API_KEY`` is optional and, when
set, is sent as an ``X-API-Key`` header.
"""

import asyncio
import threading
import httpx
from app.database.database import SessionLocal
from d4k_ms_base.logger import application_logger
from app.model.connection_manager import connection_manager
from app.database.user import User
from app.database.transmission import Transmission
from app.model.usdm_json import USDMJson
from app.configuration.configuration import application_configuration

TIMEOUT = 120.0
ERROR_LEN = 200


def backbone_enabled() -> bool:
    """True when a backbone URL has been configured."""
    return bool(application_configuration.backbone_url)


def backbone_load_url() -> str:
    """The backbone's study load endpoint."""
    return f"{application_configuration.backbone_url.rstrip('/')}/v1/studies"


def backbone_headers() -> dict:
    """Request headers for the backbone; carries the API key when configured."""
    key = application_configuration.backbone_api_key
    return {"X-API-Key": key} if key else {}


def run_backbone_transmit(version_id: int, user: User) -> None:
    t = threading.Thread(
        target=asyncio.run,
        args=(backbone_transmit(version_id, user),),
    )
    t.start()


async def backbone_transmit(version_id: int, user: User) -> None:
    session = SessionLocal()
    try:
        usdm = USDMJson(version_id, session)
        details = usdm.study_version()
        tx = Transmission.create(
            version=version_id,
            study=details["titles"]["C207616"],
            status="Preparing",
            user_id=user.id,
            session=session,
        )
        full_path, filename, _ = usdm.json()
        url = backbone_load_url()
        application_logger.info(
            f"Backbone load: sending '{filename}' from version id '{version_id}' to '{url}'"
        )
        with open(full_path, "rb") as fh:
            contents = fh.read()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                files={"file": (filename, contents, "application/json")},
                headers=backbone_headers(),
                timeout=TIMEOUT,
            )
        success, message = _outcome_message(response)
        tx.update_status(status=message, session=session)
        application_logger.info(message)
        session.close()
        if success:
            await connection_manager.success(message, str(user.id))
        else:
            await connection_manager.error(message, str(user.id))
    except Exception as e:
        application_logger.exception(
            f"Exception loading USDM from version '{version_id}' into the backbone",
            e,
        )
        session.close()
        await connection_manager.error(
            f"Error encountered loading USDM from version '{version_id}' into the backbone",
            str(user.id),
        )


def _outcome_message(response: httpx.Response) -> tuple[bool, str]:
    """Map a backbone load response to a (success, user message) pair."""
    if response.status_code in [200, 201]:
        body = response.json()
        return (
            True,
            f"Successful backbone load: study '{body.get('slug', '?')}', "
            f"{body.get('triple_count', '?')} triples in graph '{body.get('graph_uri', '?')}'",
        )
    if response.status_code == 409:
        return (
            False,
            "Backbone load rejected: this protocol version is already loaded in the backbone",
        )
    detail = response.text or ""
    if len(detail) > ERROR_LEN:
        detail = f"{detail[0:ERROR_LEN]} ..."
    return (
        False,
        f"Unsuccessful backbone load (HTTP {response.status_code}): {detail}",
    )
