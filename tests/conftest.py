"""Shared pytest setup: force offline demo mode; rate limiting off by default."""

import os
import sys

os.environ["FLASK_ENV"] = "production"
os.environ.setdefault("SESSION_SECRET", "test-secret-key")
# Ensure Supabase is treated as NOT configured so the in-memory backend is used.
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
import db  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_store():
    db.reset_demo_store()
    yield
    db.reset_demo_store()


@pytest.fixture()
def flask_app():
    import app as app_module
    from http_security import limiter
    app_module.app.config["TESTING"] = True
    limiter.enabled = False  # keep non-rate-limit tests unaffected
    yield app_module.app
    limiter.enabled = True
