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

def test_overview(client: TestClient) -> None:
    response = client.get("/dashboard/overview")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"kpis", "funnel", "statusBreakdown", "insights"}
    assert body["kpis"]["applications"] == 3
    assert body["kpis"]["open"] == 2  # Spotify (interview) and Klarna (applied)
    assert body["kpis"]["medianRejectionDays"] == pytest.approx(3.25)  # N26: Tue 10:00 → Fri 16:00
    assert [(s["stage"], s["value"], s["conversion"]) for s in body["funnel"]] == [
        ("applied", 3, None), ("replied", 2, pytest.approx(2 / 3)), ("interview", 1, 0.5), ("offer", 0, 0.0),
    ]
    assert [s["status"] for s in body["statusBreakdown"]] == ["applied", "interview", "rejected"]
    assert body["insights"]["fastestRejection"]["company"] == "N26"
    assert body["insights"]["busiestDay"] == {"date": (MONDAY + timedelta(days=1)).date().isoformat(), "count": 2}
    assert body["insights"]["bestRole"] is None

def test_overview_is_filtered(client: TestClient) -> None:
    body = client.get("/dashboard/overview", params={"companies": ["n26"]}).json()
    assert body["kpis"]["applications"] == 1
    assert body["statusBreakdown"] == [{"status": "rejected", "value": 1, "share": 1.0}]
    body = client.get("/dashboard/overview", params={"statuses": ["ghosted"]}).json()
    assert body["kpis"]["applications"] == 0
    assert body["insights"]["longestProcess"] is None

def test_timeline(client: TestClient) -> None:
    response = client.get("/dashboard/timeline", params={"weeks": 4})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"weekly", "heatmap"}
    assert len(body["weekly"]) == 4
    # MONDAY is last week's Monday
    assert body["weekly"][-2] == {
        "weekStart": MONDAY.date().isoformat(),
        "counts": {"applied": 1, "interview": 1, "rejected": 1},
    }
    assert body["weekly"][-1]["counts"] == {}
    heatmap = body["heatmap"]
    assert heatmap["end"] == NOW.date().isoformat()
    assert heatmap["days"][-1]["date"] == heatmap["end"]
    assert heatmap["max"] == 2  # Spotify on Monday; N26 and Klarna on Tuesday
    assert sum(day["count"] for day in heatmap["days"]) == 3

def test_timeline_is_filtered(client: TestClient) -> None:
    body = client.get("/dashboard/timeline", params={"companies": ["n26"]}).json()
    assert len(body["weekly"]) == 26
    assert sum(sum(week["counts"].values()) for week in body["weekly"]) == 1
    assert body["heatmap"]["max"] == 1

def test_timeline_weeks_bounds(client: TestClient) -> None:
    assert client.get("/dashboard/timeline", params={"weeks": 3}).status_code == 422
    assert client.get("/dashboard/timeline", params={"weeks": 105}).status_code == 422
    assert client.get("/dashboard/timeline", params={"weeks": 104}).status_code == 200

def test_requires_login() -> None:
    client = TestClient(_app())
    assert client.get("/dashboard/filters").status_code == 401
    assert client.get("/dashboard/patterns").status_code == 401
    assert client.get("/dashboard/overview").status_code == 401
    assert client.get("/dashboard/timeline").status_code == 401
