from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from server.routers import companies
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
    # Spotify: an old rejected process and a newer one in interviews
    _email("s1", 300, ApplicationStatus.Applied, "Spotify", "Data Engineer"),
    _email("s2", 290, ApplicationStatus.Rejected, "Spotify", "Data Engineer"),
    _email("s3", 20, ApplicationStatus.Applied, "Spotify", "Backend Engineer"),
    _email("s4", 10, ApplicationStatus.Interview, "Spotify", "Backend Engineer"),
    _email("n1", 15, ApplicationStatus.Applied, "N26", "Data Engineer"),
]


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")
    app.include_router(companies.router)
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


def test_list(client: TestClient) -> None:
    response = client.get("/companies")
    assert response.status_code == 200
    body = response.json()
    assert body == [
        {"key": "spotify", "name": "Spotify", "applications": 2, "statuses": ["interview", "rejected"]},
        {"key": "n26", "name": "N26", "applications": 1, "statuses": ["applied"]},
    ]
    assert not _keys(body) & TEXT_FIELDS

def test_list_applies_filters(client: TestClient) -> None:
    body = client.get("/companies", params={"statuses": ["rejected"]}).json()
    assert body == [{"key": "spotify", "name": "Spotify", "applications": 1, "statuses": ["rejected"]}]

def test_detail(client: TestClient) -> None:
    response = client.get("/companies/spotify")
    assert response.status_code == 200
    body = response.json()
    assert body["key"] == "spotify"
    assert body["applicationCount"] == 2
    assert body["emailCount"] == 4
    assert body["repeat"] is True
    assert [app["role"] for app in body["applications"]] == ["Backend Engineer", "Data Engineer"]
    assert [email["emailId"] for email in body["applications"][0]["emails"]] == ["s3", "s4"]
    assert body["applications"][0]["emails"][1]["title"]
    assert not _keys(body) & TEXT_FIELDS

def test_detail_ignores_filters(client: TestClient) -> None:
    body = client.get("/companies/spotify", params={"statuses": ["rejected"], "q": "nothing matches"}).json()
    assert body["applicationCount"] == 2

def test_detail_not_found(client: TestClient) -> None:
    assert client.get("/companies/nope").status_code == 404

def test_requires_login() -> None:
    client = TestClient(_app())
    assert client.get("/companies").status_code == 401
    assert client.get("/companies/spotify").status_code == 401
