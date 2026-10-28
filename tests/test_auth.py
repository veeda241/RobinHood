"""Tests for the hybrid auth layer and endpoint protection."""

DEV_EMAIL = "admin@robinhood.gov.in"
DEV_PASSWORD = "admin-demo-123"  # the documented offline-demo fallback


def test_admin_routes_require_auth(flask_app):
    client = flask_app.test_client()
    assert client.get("/api/users").status_code == 403
    assert client.get("/api/stats").status_code == 403
    assert client.put("/api/users/flag/TXP001").status_code == 403


def test_admin_login_and_access(flask_app):
    client = flask_app.test_client()
    r = client.post("/api/admin/login", json={"email": DEV_EMAIL, "password": DEV_PASSWORD})
    assert r.status_code == 200
    assert r.get_json()["role"] == "admin"
    assert client.get("/api/users").status_code == 200


def test_bad_credentials_rejected(flask_app):
    client = flask_app.test_client()
    r = client.post("/api/admin/login", json={"email": DEV_EMAIL, "password": "wrong"})
    assert r.status_code == 401


def test_whoami_reflects_session(flask_app):
    client = flask_app.test_client()
    assert client.get("/api/auth/me").get_json()["role"] is None
    client.post("/api/admin/login", json={"email": DEV_EMAIL, "password": DEV_PASSWORD})
    assert client.get("/api/auth/me").get_json()["role"] == "admin"


def test_assess_in_demo_mode_persists_and_audits(flask_app):
    import db
    client = flask_app.test_client()
    r = client.post("/api/tax/assess", json={
        "gross_income": 900000, "name": "Zoe", "tax_paid": 1000,
        "deductions": {"80C": 100000}, "pan": "ABCDE1234F"})
    assert r.status_code == 201
    body = r.get_json()
    assert body["assessment"]["recommended_regime"] in ("NEW", "OLD", "EQUAL")
    assert len(db._STORE["taxpayers"]) == 1
    assert len(db._STORE["system_audit_ledger"]) >= 1


def test_public_optimize_needs_no_auth(flask_app):
    client = flask_app.test_client()
    r = client.post("/api/tax/optimize", json={"gross_income": 1500000,
                    "deductions": {"80C": 150000, "80D": 50000}})
    assert r.status_code == 200
    assert r.get_json()["recommended_regime"] == "NEW"


def test_validation_rejects_negative_income(flask_app):
    client = flask_app.test_client()
    r = client.post("/api/tax/optimize", json={"gross_income": -5})
    assert r.status_code == 400


def test_login_is_rate_limited(flask_app):
    from http_security import limiter
    limiter.enabled = True
    try:
        limiter.reset()
        client = flask_app.test_client()
        codes = [client.post("/api/admin/login",
                 json={"email": DEV_EMAIL, "password": DEV_PASSWORD}).status_code for _ in range(8)]
        assert 429 in codes
    finally:
        limiter.enabled = False
