import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect

from server.schemas.websocket import JobState
from server.services import emails
from server.websocket import ConnectionManager

router = APIRouter(
    prefix="/emails",
    tags=["Emails"],
)

ws_manager = ConnectionManager()

@router.get("/refresh")
async def refresh_emails(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    latest_history_id = None # todo: replace with a call to the databaes to fetch this
    ws_manager.jobs[job_id] = JobState(status="pending", task_name="Sync emails")
    if latest_history_id is None:
        # fetch all (only happens once or when the database gets reset)
        # this also needs to set the latest_history_id
        background_tasks.add_task(emails.sync_all_emails, ws_manager, job_id)
    else:
        # fetch only latest using the history endpoint
        # this also needs to reset the history_id to the latest
        background_tasks.add_task(emails.sync_latest_emails, ws_manager, job_id, latest_history_id)

    return {"job_id": job_id}

@router.websocket("/ws/sync/{job_id}")
async def websocket_sync(websocket: WebSocket, job_id: str):
    await ws_manager.connect(websocket, job_id)
    try:
        # Keep the connection open and wait for client to disconnect
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, job_id)
        print(f"Client disconnected from job {job_id}. Task continues running.")