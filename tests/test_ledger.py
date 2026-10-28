"""Tests for the tamper-evident chained audit ledger."""

import db
import audit
from models import Taxpayer


def _seed_three():
    for i in range(3):
        Taxpayer.create(name=f"P{i}", gross_income=500000 + i * 100000,
                        tax_paid=10000, user_id=f"TXP00{i}", actor="tester")


def test_chain_intact_after_events():
    _seed_three()
    res = audit.verify_chain()
    assert res["ok"] is True
    assert res["length"] == 3


def test_genesis_prev_hash_is_zeros():
    _seed_three()
    first = db.select_all("system_audit_ledger", order_by="log_id")[0]
    assert first["prev_hash"] == audit.GENESIS_HASH


def test_content_tamper_is_detected():
    _seed_three()
    ledger = db._STORE["system_audit_ledger"]
    ledger[1]["payload_json"] = '{"tampered": true}'  # in-place DB edit bypassing app
    res = audit.verify_chain()
    assert res["ok"] is False
    assert res["broken_at"] == ledger[1]["log_id"]
    assert "content_tamper" in res["reason"]


def test_link_tamper_is_detected():
    _seed_three()
    ledger = db._STORE["system_audit_ledger"]
    ledger[2]["prev_hash"] = "f" * 64  # break the chain linkage
    res = audit.verify_chain()
    assert res["ok"] is False
    assert "broken_link" in res["reason"]


def test_chaining_links_each_row_to_previous():
    _seed_three()
    ledger = db.select_all("system_audit_ledger", order_by="log_id")
    for prev, cur in zip(ledger, ledger[1:]):
        assert cur["prev_hash"] == prev["payload_hash"]


def test_get_trail_is_newest_first():
    _seed_three()
    trail = audit.get_trail(limit=10)
    ids = [r["log_id"] for r in trail]
    assert ids == sorted(ids, reverse=True)
