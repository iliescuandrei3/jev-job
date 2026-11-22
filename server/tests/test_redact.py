import pytest

from server.services import redact as redact_module
from server.services.redact import redact


@pytest.fixture(autouse=True)
def _personal_env(monkeypatch):
    monkeypatch.setenv("PERSONAL_EMAIL", "me@example.com")
    monkeypatch.setenv("FIRSTNAME", "Ada")
    monkeypatch.setenv("LASTNAME", "Lovelace")
    monkeypatch.setenv("PHONE_NUMBER", "+40 700 000 000")


def test_redacts_personal_values():
    text = "Hi Ada Lovelace, write to me@example.com or call +40 700 000 000"
    assert redact(text) == "Hi [NAME] [NAME], write to [EMAIL_ADDRESS] or call [PHONE]"


@pytest.mark.parametrize(
    "number",
    ["+46 70 123 45 67", "0712-345-678", "(555) 123-4567", "+1.555.123.4567", "0712345678"],
)
def test_redacts_any_phone_number(number):
    assert redact(f"Call our recruiter at {number} today") == "Call our recruiter at [PHONE] today"


@pytest.mark.parametrize(
    "text",
    ["Interview on 2026-11-21 at 14:30", "Starts 21.11.2026", "Job ID 12345, 3 rounds", "Salary 4500 EUR"],
)
def test_keeps_short_numbers(text):
    assert redact(text) == text


def test_missing_env_values_are_skipped(monkeypatch):
    monkeypatch.delenv("PHONE_NUMBER")
    monkeypatch.delenv("LASTNAME")
    assert redact("Hi Ada") == "Hi [NAME]"


def test_pattern_is_module_level():
    assert redact_module._PHONE_PATTERN.search("+40 712 345 678")
