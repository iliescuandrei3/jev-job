from fastapi import WebSocket

from server.schemas.websocket import JobState


class ConnectionManager:

    def __init__(self):
        self.jobs: dict[str, JobState] = {}
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str) -> None:
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        
        # Send current state immediately upon connecting
        if job_id in self.jobs:
            await websocket.send_json(self.jobs[job_id].model_dump())

    def disconnect(self, websocket: WebSocket, job_id: str) -> None:
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)

    async def broadcast_progress(self, job_id: str, state: JobState) -> None:
        # Update the global state so new connections see it
        self.jobs[job_id] = state
        
        # Push the update to anyone currently listening
        if job_id in self.active_connections:
            payload = state.model_dump()
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(payload)
                except:
                    # Ignore clients that dropped abruptly
                    pass
