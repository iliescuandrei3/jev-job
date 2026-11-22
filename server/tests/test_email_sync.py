import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import httpx2
import openai
import pytest
from typesafe_sdk import TypeSafeInternalServerError, TypeSafePermissionDeniedError

from server.schemas.email import ApplicationStatus, ParsedEmail
from server.services import email_decision, email_sync


class _WsStub:
    def __init__(self):
        self.messages: list[str] = []

    async def broadcast_progress(self, job_id, state):
        self.messages.append(state.message)


def _email(email_id: str, snippet: str = "Thanks for applying") -> ParsedEmail:
    return ParsedEmail(
        emailId=email_id,
        threadId=email_id,
        labels=["INBOX"],
        snippet=snippet,
        date=datetime(2026, 11, 1, tzinfo=timezone.utc),
        internalDate="1761991200000",
        subject="Your application",
        toAddress="me@example.com",
        toName="Me",
        fromAddress="jobs@acme.com",
        fromName="Acme",
        content=[],
    )


def _decision(is_job: float):
    return SimpleNamespace(nouls={"isJob": SimpleNamespace(noul=is_job)})


@pytest.fixture
def failed(monkeypatch):
    recorded: list[tuple[str, int, str]] = []

    async def record(email_id, status_code, reason):
        recorded.append((email_id, status_code, reason))

    monkeypatch.setattr(email_sync, "record_failed_email_id", record)
    return recorded


def test_rejected_decision_is_recorded_and_skipped(monkeypatch, failed):
    async def decide(email):
        if email.emailId == "blocked":
            raise TypeSafePermissionDeniedError(403, "Request blocked by content filter: [PHONE]", httpx2.Headers())
        return _decision(0.9)

    monkeypatch.setattr(email_sync, "decide_email_application", decide)
    ws = _WsStub()

    decided = asyncio.run(email_sync._make_decisions(ws, "job", [_email("a"), _email("blocked"), _email("b")]))

    assert [e.emailId for e in decided] == ["a", "b"]
    assert [(i, c) for i, c, _ in failed] == [("blocked", 403)]
    assert "content filter" in failed[0][2]
    assert any("blocked was rejected" in m for m in ws.messages)


def test_systemic_decision_error_still_aborts(monkeypatch, failed):
    async def decide(email):
        raise TypeSafeInternalServerError(500, "boom", httpx2.Headers())

    monkeypatch.setattr(email_sync, "decide_email_application", decide)

    with pytest.raises(TypeSafeInternalServerError):
        asyncio.run(email_sync._make_decisions(_WsStub(), "job", [_email("a")]))
    assert failed == []


def test_rejected_status_is_recorded_and_skipped(monkeypatch, failed):
    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    async def get_status(client, email):
        if email.emailId == "blocked":
            response = httpx.Response(403, request=httpx.Request("POST", "https://openrouter.ai"))
            raise openai.PermissionDeniedError("blocked", response=response, body=None)
        return SimpleNamespace(applicationStatus=ApplicationStatus.Applied, company="Acme", role="Engineer")

    monkeypatch.setattr(email_sync, "openrouter", lambda: _Client())
    monkeypatch.setattr(email_sync, "get_email_status", get_status)

    done = asyncio.run(email_sync._get_email_status(_WsStub(), "job", [_email("a"), _email("blocked")]))

    assert [e.emailId for e in done] == ["a"]
    assert done[0].company == "Acme"
    assert [(i, c) for i, c, _ in failed] == [("blocked", 403)]


def test_decision_state_redacts_text_fields(monkeypatch):
    monkeypatch.setenv("PERSONAL_EMAIL", "me@example.com")
    email = _email("a", snippet="Call us at +46 70 123 45 67")

    state = email_decision._decision_state(email)

    assert state["snippet"] == "Call us at [PHONE]"
    assert state["toAddress"] == "[EMAIL_ADDRESS]"
    assert state["internalDate"] == "1761991200000"
    assert "content" not in state
