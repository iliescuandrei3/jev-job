from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from server.routers import applications
from server.routers.auth import get_current_user
from server.schemas.email import ApplicationStatus, JobEmail
from server.services import dashboard

NOW = datetime.now(timezone.utc)
TEXT_FIELDS = {"subject", "snippet", "content", "body", "fromAddress", "fromName", "toAddress", "toName"}

JsonValue = dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None


def _email(email_id: str, days_ago: float, status: ApplicationStatus, company: str, role: str) -> JobEmail:
    return JobEmail(
        emailId=email_id,
        date=NOW - timedelta(days=days_ago),
        applicationStatus=status,
        company=company,
        role=role,
        fromAddress=f"jobs@{company.lower()}.com",
    )

EMAILS = [
    _email("s1", 20, ApplicationStatus.Applied, "Spotify", "Backend Engineer"),
    _email("s2", 10, ApplicationStatus.Interview, "Spotify", "Backend Engineer"),
    _email("n1", 15, ApplicationStatus.Applied, "N26", "Data Engineer"),
]


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")
    app.include_router(applications.router)
    return app

@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    async def fake_get_job_emails() -> list[JobEmail]:
        return EMAILS

    monkeypatch.setattr(dashboard, "get_job_emails", fake_get_job_emails)
    app = _app()
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test"}
    return TestClient(app)

def _keys(value: JsonValue) -> set[str]:
    """Every key anywhere in a JSON value."""
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}
    return set()

def _assert_no_text_fields(body: JsonValue) -> None:
    keys = _keys(body)
    assert not keys & TEXT_FIELDS


def test_list(client: TestClient) -> None:
    response = client.get("/applications")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["id"] for item in body["items"]] == ["n1", "s1"]
    assert body["items"][1]["emailCount"] == 2
    _assert_no_text_fields(body)

def test_list_applies_filters(client: TestClient) -> None:
    body = client.get("/applications", params={"companies": ["spotify"]}).json()
    assert body["total"] == 1
    assert body["items"][0]["companyKey"] == "spotify"

def test_list_sort_and_limit(client: TestClient) -> None:
    body = client.get("/applications", params={"sort": "duration", "limit": 1}).json()
    assert body["total"] == 2
    assert [item["id"] for item in body["items"]] == ["s1"]

def test_list_rejects_bad_params(client: TestClient) -> None:
    assert client.get("/applications", params={"sort": "nope"}).status_code == 422
    assert client.get("/applications", params={"limit": 0}).status_code == 422
    assert client.get("/applications", params={"offset": -1}).status_code == 422

def test_list_unknown_role_filter(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    no_role = _email("k1", 5, ApplicationStatus.Applied, "Klarna", "")

    async def fake_get_job_emails() -> list[JobEmail]:
        return [*EMAILS, no_role]

    monkeypatch.setattr(dashboard, "get_job_emails", fake_get_job_emails)
    body = client.get("/applications", params={"unknownRole": "true"}).json()
    assert [item["id"] for item in body["items"]] == ["k1"]
    body = client.get("/applications", params={"roles": ["Data Engineer"], "unknownRole": "true"}).json()
    assert [item["id"] for item in body["items"]] == ["k1", "n1"]
    assert client.get("/applications").json()["total"] == 3

def test_detail(client: TestClient) -> None:
    response = client.get("/applications/s1")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "s1"
    assert [email["emailId"] for email in body["emails"]] == ["s1", "s2"]
    _assert_no_text_fields(body)

def test_detail_not_found(client: TestClient) -> None:
    assert client.get("/applications/nope").status_code == 404

def test_requires_login() -> None:
    client = TestClient(_app())
    assert client.get("/applications").status_code == 401
    assert client.get("/applications/s1").status_code == 401
