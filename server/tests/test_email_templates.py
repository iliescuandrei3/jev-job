from server.schemas.application import ApplicationEmailOut
from server.schemas.email import ApplicationStatus
from server.services.email_templates import email_text


def test_deterministic() -> None:
    first = email_text("18f3abc", ApplicationStatus.Interview, "Spotify", "Backend Engineer")
    assert all(email_text("18f3abc", ApplicationStatus.Interview, "Spotify", "Backend Engineer") == first for _ in range(5))

def test_every_status_with_and_without_role() -> None:
    for status in ApplicationStatus:
        for email_id in ("a", "b", "c", "d", "e"):
            title, description = email_text(email_id, status, "Spotify", "Backend Engineer")
            assert "Spotify" in title
            assert "{" not in title + description

            _, without_role = email_text(email_id, status, "Spotify", "")
            assert "{" not in without_role
            assert "  " not in without_role and " ." not in without_role

def test_email_out_has_no_text_fields() -> None:
    fields = set(ApplicationEmailOut.model_fields)
    assert not fields & {"subject", "snippet", "content"}
    assert not any(field.startswith(("from", "to")) for field in fields)
