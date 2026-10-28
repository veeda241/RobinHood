"""
RobinHood AI - Cryptographic Audit Ledger (tamper-evident, append-only)

Every critical action appends a row to `system_audit_ledger`. Each row's
payload_hash folds in the PREVIOUS row's payload_hash, so the table is a hash
chain: rewriting, reordering, or deleting any historical row breaks every hash
after it, and `verify_chain()` pinpoints the first broken `log_id`. This is the
property that makes the trail tamper-evident rather than merely hashed.

Hash input (canonical, order-stable):
    SHA256( prev_hash || canonical_timestamp || action_type || actor_id
            || (target_user_id or '') || payload_json )
Genesis row uses prev_hash = 64 x '0'. `payload_json` is json.dumps(sort_keys=True)
so dict ordering never changes the digest.
"""

import json
import hashlib
from datetime import datetime, timezone

import db

GENESIS_HASH = "0" * 64


def _canon_ts(dt: datetime) -> str:
    """Normalise a timestamp to a stable UTC ISO-8601 string for hashing."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _parse_ts(value) -> datetime:
    if isinstance(value, datetime):
        return value
    # PostgREST returns ISO-8601; python 3.11 fromisoformat accepts 'Z'.
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def compute_hash(prev_hash: str, timestamp: datetime, action_type: str,
                 actor_id: str, target_user_id, payload_json: str) -> str:
    material = "|".join([
        prev_hash,
        _canon_ts(timestamp),
        action_type,
        actor_id or "",
        str(target_user_id) if target_user_id is not None else "",
        payload_json,
    ])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def record_event(action_type: str, actor_id: str, target_user_id, payload: dict) -> dict:
    """Append one chained event and return the stored row."""
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    tail = db.select_last("system_audit_ledger", order_by="log_id")
    prev_hash = tail["payload_hash"] if tail else GENESIS_HASH
    now = datetime.now(timezone.utc)
    row = {
        "timestamp": _canon_ts(now),
        "actor_id": actor_id,
        "action_type": action_type,
        "target_user_id": str(target_user_id) if target_user_id is not None else None,
        "payload_json": payload_json,
        "prev_hash": prev_hash,
        "payload_hash": compute_hash(prev_hash, now, action_type, actor_id, target_user_id, payload_json),
    }
    return db.insert_row("system_audit_ledger", row)


def verify_chain() -> dict:
    """Recompute the whole chain. Returns {ok, length, broken_at, reason}."""
    rows = db.select_all("system_audit_ledger", order_by="log_id")
    prev_hash = GENESIS_HASH
    for row in rows:
        expected = compute_hash(
            prev_hash,
            _parse_ts(row["timestamp"]),
            row["action_type"],
            row["actor_id"],
            row.get("target_user_id"),
            row["payload_json"],
        )
        if row.get("prev_hash") != prev_hash:
            return {"ok": False, "length": len(rows), "broken_at": row.get("log_id"),
                    "reason": "broken_link: prev_hash does not match preceding row"}
        if row.get("payload_hash") != expected:
            return {"ok": False, "length": len(rows), "broken_at": row.get("log_id"),
                    "reason": "content_tamper: payload_hash does not match recomputed digest"}
        prev_hash = row["payload_hash"]
    return {"ok": True, "length": len(rows), "broken_at": None,
            "reason": "chain intact", "head_hash": prev_hash}


def get_trail(limit: int = 50) -> list[dict]:
    """Most-recent events (hashes included) for the admin dashboard / CLI."""
    rows = db.select_all("system_audit_ledger", order_by="log_id")
    return list(reversed(rows[-limit:]))
