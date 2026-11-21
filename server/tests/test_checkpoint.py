import asyncio
from datetime import datetime, timezone

import pytest

from server.db import checkpoint
from server.db.models import HistoryCheckpoint

SYNCED_AT = datetime(2026, 11, 21, 12, tzinfo=timezone.utc)


def _stub_store(monkeypatch: pytest.MonkeyPatch, stored: HistoryCheckpoint | None) -> list[HistoryCheckpoint]:
    saved: list[HistoryCheckpoint] = []

    async def fake_get(_document_id: str) -> HistoryCheckpoint | None:
        return stored

    async def fake_save(self: HistoryCheckpoint) -> HistoryCheckpoint:
        saved.append(self)
        return self

    monkeypatch.setattr(HistoryCheckpoint, "get", fake_get)
    monkeypatch.setattr(HistoryCheckpoint, "save", fake_save)
    return saved

def test_no_history_id_keeps_the_stored_one(monkeypatch: pytest.MonkeyPatch) -> None:
    saved = _stub_store(monkeypatch, HistoryCheckpoint.model_construct(id="gmail", historyId="123", lastSyncedAt=None))
    asyncio.run(checkpoint.update_history_checkpoint(None, SYNCED_AT))
    assert (saved[0].historyId, saved[0].lastSyncedAt) == ("123", SYNCED_AT)

def test_new_history_id_is_saved(monkeypatch: pytest.MonkeyPatch) -> None:
    saved = _stub_store(monkeypatch, HistoryCheckpoint.model_construct(id="gmail", historyId="123", lastSyncedAt=None))
    asyncio.run(checkpoint.update_history_checkpoint("456", SYNCED_AT))
    assert (saved[0].historyId, saved[0].lastSyncedAt) == ("456", SYNCED_AT)
