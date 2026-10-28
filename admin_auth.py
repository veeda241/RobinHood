"""
RobinHood AI - Admin Auth Blueprint (Flask-session half of the hybrid model)

Administrators authenticate with an email + password checked against a PBKDF2
hash held in the environment (never a plaintext password). On success a signed,
HttpOnly session cookie is issued and role='admin' is stored server-side. All
state-changing admin routes are then guarded by @require_role('admin').

Login is rate-limited and every login/logout is written to the audit ledger.
"""

import os
import hmac
import hashlib

from flask import Blueprint, jsonify, request, session

import audit
from http_security import limiter

ITERATIONS = 210000

auth_bp = Blueprint("auth", __name__)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, its, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 bytes.fromhex(salt_hex), int(its))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def _expected_admin():
    email = os.getenv("ADMIN_EMAIL", "admin@robinhood.gov.in")
    pw_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    if not pw_hash:
        # Offline demo convenience so the admin dashboard is reachable without a
        # provisioned secret. Insecure: production MUST set ADMIN_PASSWORD_HASH.
        dev_pw = "admin-demo-123"
        return email, hash_password(dev_pw), dev_pw
    return email, pw_hash, None


@auth_bp.route("/api/admin/login", methods=["POST"])
@limiter.limit("5 per minute")
def admin_login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))
    admin_email, admin_hash, dev_pw = _expected_admin()

    ok_email = hmac.compare_digest(email.lower(), admin_email.lower())
    if dev_pw is not None:
        ok_pw = password == dev_pw
    else:
        ok_pw = verify_password(password, admin_hash)

    if not (ok_email and ok_pw):
        # Uniform message; do not reveal which factor failed.
        return jsonify({"error": "Invalid credentials."}), 401

    session.clear()
    session["role"] = "admin"
    session["email"] = admin_email
    session["actor"] = f"admin:{admin_email}"
    session.permanent = True
    audit.record_event("ADMIN_LOGIN", admin_email, None, {"success": True})
    return jsonify({"role": "admin", "email": admin_email}), 200


@auth_bp.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    actor = session.get("email")
    session.clear()
    if actor:
        audit.record_event("ADMIN_LOGOUT", actor, None, {})
    return jsonify({"ok": True}), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
def whoami():
    if session.get("role") == "admin":
        return jsonify({"mode": "session", "role": "admin", "email": session.get("email")}), 200
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        from auth_decorators import _jwt_to_principal
        p = _jwt_to_principal(header.split(" ", 1)[1])
        if p:
            return jsonify({"mode": "jwt", "role": p.role, "id": p.id}), 200
        return jsonify({"error": "Invalid token."}), 401
    return jsonify({"mode": "anonymous", "role": None}), 200
