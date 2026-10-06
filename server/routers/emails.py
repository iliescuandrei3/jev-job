import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)

from server.schemas.websocket import JobState
from server.services import email_sync
from server.websocket import ActiveJobInProgress, ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/emails",
    tags=["Emails"],
)

ws_manager = ConnectionManager()


async def _run_refresh(job_id: str, latest_history_id: str | None) -> None:
    try:
        if latest_history_id is None:
            await email_sync.sync_all_emails(ws_manager, job_id)
        else:
            await email_sync.sync_latest_emails(ws_manager, job_id, latest_history_id)

        current_state = ws_manager.get_job_state(job_id)
        if current_state is None or current_state.status not in ("completed", "failed"):
            await ws_manager.broadcast_progress(
                job_id,
                JobState(
                    status="completed",
                    task_name="Sync emails",
                    message="Email refresh completed.",
                ),
            )
    except Exception:
        logger.exception("Email refresh job %s failed", job_id)
        await ws_manager.broadcast_progress(
            job_id,
            JobState(
                status="failed",
                task_name="Sync emails",
                message="Email refresh failed. Check the server logs for details.",
            ),
        )


@router.post("/refresh")
async def refresh_emails(background_tasks: BackgroundTasks):
    try:
        job_id = ws_manager.create_job("Sync emails")
    except ActiveJobInProgress as error:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "An email refresh is already in progress.",
                "job_id": error.job_id,
            },
        ) from error

    latest_history_id = None  # TODO: fetch this from the database.
    background_tasks.add_task(_run_refresh, job_id, latest_history_id)

    return {"job_id": job_id}


@router.websocket("/ws/sync/{job_id}")
async def websocket_sync(websocket: WebSocket, job_id: str):
    try:
        await ws_manager.connect(websocket, job_id)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket, job_id)