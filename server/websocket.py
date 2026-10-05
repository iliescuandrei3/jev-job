import uuid

from fastapi import WebSocket, WebSocketDisconnect

from server.schemas.websocket import JobState


class ActiveJobInProgress(Exception):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Job {job_id} is already in progress")


class ConnectionManager:
    def __init__(self, max_terminal_jobs: int = 100) -> None:
        if max_terminal_jobs < 1:
            raise ValueError("max_terminal_jobs must be at least one")
        self._jobs: dict[str, JobState] = {}
        self._active_connections: dict[str, list[WebSocket]] = {}
        self._active_job_id: str | None = None
        self._max_terminal_jobs = max_terminal_jobs

    def create_job(self, task_name: str) -> str:
        if self._active_job_id is not None:
            active_job = self._jobs.get(self._active_job_id)
            if active_job is not None and active_job.status in ("pending", "running"):
                raise ActiveJobInProgress(self._active_job_id)

        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobState(status="pending", task_name=task_name)
        self._active_job_id = job_id
        return job_id

    def get_job_state(self, job_id: str) -> JobState | None:
        state = self._jobs.get(job_id)
        return state.model_copy() if state is not None else None

    async def connect(self, websocket: WebSocket, job_id: str) -> None:
        state = self._jobs.get(job_id)
        await websocket.accept()
        if state is None:
            await websocket.send_json(
                JobState(
                    status="failed",
                    task_name="Sync emails",
                    message="This refresh job is no longer available. Start a new refresh.",
                ).model_dump()
            )
            await websocket.close(code=1008)
            return

        self._active_connections.setdefault(job_id, []).append(websocket)
        await websocket.send_json(state.model_dump())

    def disconnect(self, websocket: WebSocket, job_id: str) -> None:
        connections = self._active_connections.get(job_id)
        if connections is not None and websocket in connections:
            connections.remove(websocket)
            if not connections:
                del self._active_connections[job_id]

    async def broadcast_progress(self, job_id: str, state: JobState) -> None:
        if job_id not in self._jobs:
            raise KeyError(f"Unknown job ID: {job_id}")

        if state.status in ("completed", "failed"):
            del self._jobs[job_id]
            self._jobs[job_id] = state.model_copy()
            if self._active_job_id == job_id:
                self._active_job_id = None
            await self._prune_terminal_jobs()
        else:
            self._jobs[job_id] = state.model_copy()

        if job_id in self._active_connections:
            payload = state.model_dump()
            for connection in list(self._active_connections[job_id]):
                try:
                    await connection.send_json(payload)
                except (WebSocketDisconnect, RuntimeError, OSError):
                    self.disconnect(connection, job_id)

    async def _prune_terminal_jobs(self) -> None:
        terminal_job_ids = [
            job_id
            for job_id, state in self._jobs.items()
            if state.status in ("completed", "failed")
        ]
        while len(terminal_job_ids) > self._max_terminal_jobs:
            expired_job_id = terminal_job_ids.pop(0)
            del self._jobs[expired_job_id]
            for connection in self._active_connections.pop(expired_job_id, []):
                try:
                    await connection.close(code=1000, reason="Job state expired")
                except (WebSocketDisconnect, RuntimeError, OSError):
                    pass
