"""
RobinHood AI - Authentication Decorators (hybrid model)

  * @require_supabase_auth - for citizen / machine-to-machine API traffic.
    Validates a Supabase JWT passed as `Authorization: Bearer <token>`.
  * @require_role('admin')  - for the admin dashboard and CLI-facing routes.
    Accepts either a signed Flask session cookie (admin login) OR a Supabase
    JWT carrying app_metadata.role == 'admin'.

In offline/demo mode (Supabase not configured) the JWT paths short-circuit to a
clearly-labelled demo principal so the pipeline stays runnable, while the admin
session path (which does not depend on Supabase) still enforces login.
"""

from functools import wraps

from flask import g, jsonify, request, session

import db


class _Principal:
    def __init__(self, user_id: str, email: str | None, role: str):
        self.id = user_id
        self.email = email
        self.role = role


def _jwt_to_principal(token: str) -> _Principal | None:
    try:
        client = db.get_supabase_client()
    except db.StorageError:
        return None
    try:
        res = client.auth.get_user(token)
    except Exception:
        return None
    user = getattr(res, "user", None) or (res.get("user") if isinstance(res, dict) else None)
    if not user:
        return None
    uid = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
    email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
    meta = getattr(user, "app_metadata", None) or (user.get("app_metadata") if isinstance(user, dict) else {}) or {}
    return _Principal(str(uid), email, (meta or {}).get("role", "citizen"))


def require_supabase_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if db.demo_mode():
            g.current_user = _Principal("demo-citizen", "demo@localhost", "citizen")
            return f(*args, **kwargs)
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Authentication required."}), 401
        principal = _jwt_to_principal(header.split(" ", 1)[1])
        if not principal:
            return jsonify({"error": "Invalid or expired token."}), 401
        g.current_user = principal
        return f(*args, **kwargs)
    return wrapper


def require_role(role: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") == role:
                g.current_user = _Principal(session.get("actor", f"session-{role}"),
                                            session.get("email"), role)
                return f(*args, **kwargs)
            header = request.headers.get("Authorization", "")
            if header.startswith("Bearer "):
                principal = _jwt_to_principal(header.split(" ", 1)[1])
                if principal and principal.role == role:
                    g.current_user = principal
                    return f(*args, **kwargs)
            return jsonify({"error": "Forbidden: insufficient privileges."}), 403
        return wrapper
    return decorator
