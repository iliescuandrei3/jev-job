from datetime import datetime

from server.db.models import HistoryCheckpoint


async def get_history_checkpoint() -> str | None:
    history_checkpoint = await HistoryCheckpoint.get("gmail")
    if history_checkpoint:
        return history_checkpoint.historyId
    return None

async def get_last_synced_at() -> datetime | None:
    history_checkpoint = await HistoryCheckpoint.get("gmail")
    if history_checkpoint:
        return history_checkpoint.lastSyncedAt
    return None

async def update_history_checkpoint(history_id: str | None, synced_at: datetime) -> None:
    """Always records `synced_at`. Keeps the stored history id when `history_id` is None (no new history)."""
    history_checkpoint = await HistoryCheckpoint.get("gmail")
    if history_checkpoint is None:
        history_checkpoint = HistoryCheckpoint(id="gmail")

    if history_id is not None:
        history_checkpoint.historyId = history_id
    history_checkpoint.lastSyncedAt = synced_at

    await history_checkpoint.save()
