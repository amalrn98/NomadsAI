from app.auth import _verified_email


def test_verified_email_is_returned_only_after_confirmation():
    user = {
        "email": "traveler@example.com",
        "email_confirmed_at": "2026-11-23T10:00:00Z",
    }
    assert _verified_email(user) == "traveler@example.com"


def test_unverified_email_is_not_returned():
    user = {"email": "traveler@example.com", "email_confirmed_at": None}
    assert _verified_email(user) is None


def test_missing_or_blank_email_is_not_returned():
    assert _verified_email({"email": None, "email_confirmed_at": "2026-11-23"}) is None
    assert _verified_email({"email": "  ", "email_confirmed_at": "2026-11-23"}) is None
