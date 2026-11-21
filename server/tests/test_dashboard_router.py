from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from server.routers import dashboard as dashboard_router
from server.routers.auth import get_current_user
from server.schemas.email import ApplicationStatus, JobEmail
from server.services import dashboard

NOW = datetime.now(timezone.utc)


def _email(email_id: str, date: datetime, status: ApplicationStatus, company: str, role: str) -> JobEmail:
    return JobEmail(
        emailId=email_id,
        date=date,
        applicationStatus=status,
        company=company,
        role=role,
        fromAddress=f"jobs@{company.lower()}.com",
    )

# A recent Monday at 00:00 UTC, so every email stays inside a 30-day range
MONDAY = (NOW - timedelta(days=NOW.weekday() + 7)).replace(hour=0, minute=0, second=0, microsecond=0)

EMAILS = [
    _email("s1", MONDAY.replace(hour=9), ApplicationStatus.Applied, "Spotify", "Backend Engineer"),
    _email("s2", MONDAY + timedelta(days=2, hours=14), ApplicationStatus.Interview, "Spotify", "Backend Engineer"),
    _email("n1", MONDAY + timedelta(days=1, hours=10), ApplicationStatus.Applied, "N26", "Data Engineer"),
    _email("n2", MONDAY + timedelta(days=4, hours=16), ApplicationStatus.Rejected, "N26", "Data Engineer"),
    # No role
    _email("k1", MONDAY + timedelta(days=1, hours=11), ApplicationStatus.Applied, "Klarna", ""),
]


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")
    app.include_router(dashboard_router.router)
    return app

@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    async def fake_get_job_emails() -> list[JobEmail]:
        return EMAILS

    monkeypatch.setattr(dashboard, "get_job_emails", fake_get_job_emails)
    app = _app()
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test"}
    return TestClient(app)


def test_filters_list_unknown_role(client: TestClient) -> None:
    body = client.get("/dashboard/filters").json()
    assert body["roles"] == ["Backend Engineer", "Data Engineer"]
    assert body["unknownRole"] is True

def test_patterns(client: TestClient) -> None:
    response = client.get("/dashboard/patterns")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"roles", "weekdays", "hours"}
    assert body["roles"] == [
        {"role": "", "count": 1, "interviewRate": 0.0},
        {"role": "Backend Engineer", "count": 1, "interviewRate": 1.0},
        {"role": "Data Engineer", "count": 1, "interviewRate": 0.0},
    ]
    assert [(d["day"], d["applied"], d["rejections"]) for d in body["weekdays"]] == [
        ("mon", 1, 0), ("tue", 2, 0), ("wed", 0, 0), ("thu", 0, 0), ("fri", 0, 1), ("sat", 0, 0), ("sun", 0, 0),
    ]
    assert len(body["hours"]) == 24
    assert body["hours"][14] == {"hour": 14, "interview": 1, "rejected": 0}
    assert body["hours"][16] == {"hour": 16, "interview": 0, "rejected": 1}

def test_patterns_are_filtered(client: TestClient) -> None:
    body = client.get("/dashboard/patterns", params={"unknownRole": "true"}).json()
    assert [r["role"] for r in body["roles"]] == [""]
    body = client.get("/dashboard/patterns", params={"companies": ["n26"]}).json()
    assert [r["role"] for r in body["roles"]] == ["Data Engineer"]
    assert sum(d["applied"] for d in body["weekdays"]) == 1

def test_requires_login() -> None:
    client = TestClient(_app())
    assert client.get("/dashboard/filters").status_code == 401
    assert client.get("/dashboard/patterns").status_code == 401
