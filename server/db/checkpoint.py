from server.db.models import HistoryCheckpoint


async def get_history_checkpoint() -> str | None:
    history_checkpoint = await HistoryCheckpoint.get("gmail")
    if history_checkpoint:
        return history_checkpoint.historyId
    return None

async def update_history_checkpoint(history_id: str) -> None:
    history_checkpoint = await HistoryCheckpoint.get("gmail")
    if history_checkpoint is None:
        history_checkpoint = HistoryCheckpoint(
            id="gmail",
            historyId=history_id,
        )
    else:
        history_checkpoint.historyId = history_id

    await history_checkpoint.save()