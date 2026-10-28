"""
RobinHood AI - Data Access Layer

Supabase (Postgres via PostgREST) is the system of record. Every read/write to
a table funnels through the four helpers here so that:

  * the service-role client is created once (module singleton),
  * PostgREST errors are normalised into a single StorageError the routes can
    turn into a clean 400/500 WITHOUT echoing raw driver strings to clients,
  * and, when Supabase is not configured (offline demo / CI), the exact same
    API is served from an in-memory store so the whole pipeline stays runnable.

Switching between backends is invisible to models.py / audit.py / app.py.
"""

import os
import threading

from dotenv import load_dotenv

load_dotenv()

_LOCK = threading.RLock()


class StorageError(RuntimeError):
    """Normalised storage failure. Safe message, never leaks driver internals."""


def is_supabase_configured() -> bool:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    return bool(url and key and "YOUR-PROJECT-REF" not in url and "your-service-role-key" not in key)


def demo_mode() -> bool:
    """True when running against the in-memory store instead of Supabase."""
    return not is_supabase_configured()


_CLIENT = None


def get_supabase_client():
    """Return the thread-safe service-role Supabase client (singleton)."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise StorageError("Supabase credentials are not configured.")
    try:
        from supabase import create_client
    except ImportError as exc:  # pragma: no cover
        raise StorageError("supabase client library is not installed.") from exc
    _CLIENT = create_client(url, key)
    return _CLIENT


# --- In-memory demo backend ---------------------------------------------------

TABLES = ("taxpayers", "system_audit_ledger", "compliance_notices")
_AUTO_ID = {"system_audit_ledger": "log_id", "compliance_notices": "notice_id"}

_STORE: dict[str, list[dict]] = {t: [] for t in TABLES}
_SEQ: dict[str, int] = {t: 0 for t in TABLES}


def reset_demo_store():
    """Clear the in-memory store (used by tests and the seeder)."""
    with _LOCK:
        for t in TABLES:
            _STORE[t] = []
            _SEQ[t] = 0


# --- Normalised table operations ---------------------------------------------

def select_all(table: str, order_by: str | None = None) -> list[dict]:
    if table not in TABLES:
        raise StorageError(f"Unknown table '{table}'.")
    if demo_mode():
        with _LOCK:
            rows = [dict(r) for r in _STORE[table]]
        if order_by:
            rows.sort(key=lambda r: r.get(order_by))
        return rows
    try:
        query = get_supabase_client().table(table).select("*")
        if order_by:
            query = query.order(order_by)
        return query.execute().data or []
    except Exception as exc:
        raise StorageError(f"Failed to read '{table}'.") from exc


def select_one(table: str, column: str, value) -> dict | None:
    if table not in TABLES:
        raise StorageError(f"Unknown table '{table}'.")
    if demo_mode():
        with _LOCK:
            for r in _STORE[table]:
                if str(r.get(column)) == str(value):
                    return dict(r)
        return None
    try:
        res = get_supabase_client().table(table).select("*").eq(column, value).limit(1).execute()
        return (res.data or [None])[0]
    except Exception as exc:
        raise StorageError(f"Failed to read '{table}'.") from exc


def select_last(table: str, order_by: str) -> dict | None:
    """Highest `order_by` row - used to fetch the ledger tail hash."""
    rows = select_all(table, order_by=order_by)
    return rows[-1] if rows else None


def insert_row(table: str, row: dict) -> dict:
    if table not in TABLES:
        raise StorageError(f"Unknown table '{table}'.")
    if demo_mode():
        with _LOCK:
            record = dict(row)
            id_col = _AUTO_ID.get(table)
            if id_col and record.get(id_col) is None:
                _SEQ[table] += 1
                record[id_col] = _SEQ[table]
            _STORE[table].append(record)
            return dict(record)
    try:
        res = get_supabase_client().table(table).insert(row).execute()
        return res.data[0]
    except Exception as exc:
        raise StorageError(f"Failed to write to '{table}'.") from exc


def update_row(table: str, column: str, value, changes: dict) -> dict | None:
    if table not in TABLES:
        raise StorageError(f"Unknown table '{table}'.")
    if demo_mode():
        with _LOCK:
            for r in _STORE[table]:
                if str(r.get(column)) == str(value):
                    r.update(changes)
                    return dict(r)
        return None
    try:
        res = (
            get_supabase_client()
            .table(table)
            .update(changes)
            .eq(column, value)
            .execute()
        )
        data = res.data or []
        return data[0] if data else None
    except Exception as exc:
        raise StorageError(f"Failed to update '{table}'.") from exc
