"""
RobinHood AI - Domain Models (Supabase-backed)

`Taxpayer` is the single repository for the `taxpayers` table. It owns:

  * encryption-on-write / decryption-on-read of PII (name, PAN, asset value),
  * the deterministic expected-tax + compliance computation from the tax agent,
  * the ML risk scoring and human-readable reasons,
  * and the audit-ledger write for every mutation.

Routes never touch crypto or the ledger directly - they call these methods -
so every state change is guaranteed to be encrypted and logged.
"""

from __future__ import annotations

import uuid

import db
import audit
import crypto
from tax_agent import agent, get_compliance_status


class Taxpayer:
    def __init__(self, row: dict):
        self._row = row
        self.user_id = row["user_id"]
        self.gross_income = float(row.get("gross_income", 0) or 0)
        self.declared_deductions = float(row.get("declared_deductions", 0) or 0)
        self.tax_paid = float(row.get("tax_paid_to_date", 0) or 0)
        self.expected_tax = float(row.get("expected_tax", 0) or 0)
        self.risk_score = int(row.get("calculated_risk_score", 0) or 0)
        self.recommended_regime = row.get("recommended_regime", "NEW")
        self.compliance_status = row.get("compliance_status", "COMPLIANT")

    # --- decrypted PII accessors (never stored/logged in the clear) ---------
    @property
    def name(self) -> str | None:
        return crypto.decrypt_field("name", self._row.get("name_encrypted"))

    @property
    def pan(self) -> str | None:
        return crypto.decrypt_field("pan", self._row.get("pan_encrypted"))

    @property
    def assets_value(self) -> str | None:
        return crypto.decrypt_field("assets", self._row.get("assets_value_encrypted"))

    @property
    def flagged(self) -> bool:
        return self.compliance_status == "FLAGGED_FOR_REVIEW"

    @property
    def due_amount(self) -> float:
        return max(0.0, self.expected_tax - self.tax_paid)

    def to_dict(self, include_pii: bool = True) -> dict:
        out = {
            "user_id": self.user_id,
            "declared_income": self.gross_income,
            "declared_deductions": self.declared_deductions,
            "expected_tax": self.expected_tax,
            "tax_paid": self.tax_paid,
            "due_amount": self.due_amount,
            "compliance_status": self.compliance_status,
            "flagged": self.flagged,
            "risk_score": self.risk_score,
            "recommended_regime": self.recommended_regime,
        }
        if include_pii:
            out["name"] = self.name
            # Only the blind index and a masked PAN are exposed - never the raw PAN.
            out["pan_masked"] = _mask_pan(self.pan)
        return out

    # --- persistence --------------------------------------------------------

    @classmethod
    def create(cls, name: str, gross_income: float, tax_paid: float = 0,
               deductions: dict | float | None = None, user_id: str | None = None,
               pan: str | None = None, assets_value=None, actor: str = "system") -> "Taxpayer":
        deductions_value = _normalise_deductions(deductions)
        deduction_total = _deduction_total(deductions_value)
        deductions_dict = deductions_value if isinstance(deductions_value, dict) else {"80C": deduction_total}
        new_id = user_id or str(uuid.uuid4())
        expected = agent.compute_new_regime(gross_income)["total_tax"]
        optimization = agent.optimize_regime_matrix(gross_income, deductions_dict)
        risk = agent.evaluate_compliance_risk(gross_income, deduction_total, tax_paid)
        status = _base_status(tax_paid, expected)
        row = {
            "user_id": new_id,
            "name_encrypted": crypto.encrypt_field("name", name),
            "pan_encrypted": crypto.encrypt_field("pan", pan),
            "pan_blind_index": crypto.pan_blind_index(pan),
            "assets_value_encrypted": crypto.encrypt_field("assets", assets_value),
            "gross_income": gross_income,
            "declared_deductions": deduction_total,
            "tax_paid_to_date": tax_paid,
            "expected_tax": expected,
            "calculated_risk_score": risk,
            "recommended_regime": optimization["recommended_regime"],
            "compliance_status": status,
        }
        saved = db.insert_row("taxpayers", row)
        tp = cls(saved)
        audit.record_event("TAXPAYER_CREATED", actor, new_id,
                           {"gross_income": gross_income, "expected_tax": expected,
                            "risk_score": risk, "compliance_status": status})
        return tp

    def save(self, actor: str = "system") -> "Taxpayer":
        changes = {
            "gross_income": self.gross_income,
            "tax_paid_to_date": self.tax_paid,
            "expected_tax": self.expected_tax,
            "compliance_status": self.compliance_status,
            "calculated_risk_score": self.risk_score,
        }
        db.update_row("taxpayers", "user_id", self.user_id, changes)
        audit.record_event("TAXPAYER_UPDATED", actor, self.user_id, changes)
        return self

    @staticmethod
    def get_all() -> list["Taxpayer"]:
        return [Taxpayer(r) for r in db.select_all("taxpayers", order_by="user_id")]

    @staticmethod
    def get_by_id(user_id: str) -> "Taxpayer | None":
        row = db.select_one("taxpayers", "user_id", user_id)
        return Taxpayer(row) if row else None

    @staticmethod
    def find_by_pan(pan: str) -> "Taxpayer | None":
        """Blind-index search: locate a taxpayer from their PAN without decrypting
        any stored value."""
        idx = crypto.pan_blind_index(pan)
        row = db.select_one("taxpayers", "pan_blind_index", idx)
        return Taxpayer(row) if row else None

    @staticmethod
    def toggle_flag(user_id: str, actor: str = "system") -> "Taxpayer | None":
        tp = Taxpayer.get_by_id(user_id)
        if not tp:
            return None
        if tp.flagged:
            tp.compliance_status = _base_status(tp.tax_paid, tp.expected_tax)
        else:
            tp.compliance_status = "FLAGGED_FOR_REVIEW"
        db.update_row("taxpayers", "user_id", user_id, {"compliance_status": tp.compliance_status})
        audit.record_event("FLAG_TOGGLED", actor, user_id,
                           {"compliance_status": tp.compliance_status})
        return tp

    @staticmethod
    def record_payment(user_id: str, amount: float, actor: str = "system") -> "Taxpayer | None":
        tp = Taxpayer.get_by_id(user_id)
        if not tp:
            return None
        tp.tax_paid = tp.tax_paid + float(amount)
        tp.expected_tax = agent.compute_new_regime(tp.gross_income)["total_tax"]
        tp.risk_score = agent.evaluate_compliance_risk(
            tp.gross_income, tp.declared_deductions, tp.tax_paid)
        if not tp.flagged:
            tp.compliance_status = _base_status(tp.tax_paid, tp.expected_tax)
        db.update_row("taxpayers", "user_id", user_id, {
            "tax_paid_to_date": tp.tax_paid,
            "expected_tax": tp.expected_tax,
            "calculated_risk_score": tp.risk_score,
            "compliance_status": tp.compliance_status,
        })
        audit.record_event("PAYMENT_RECORDED", actor, user_id,
                           {"amount": amount, "tax_paid_to_date": tp.tax_paid})
        return tp

    def recompute_assessment(self, actor: str = "system") -> dict:
        """Run the optimisation matrix + risk model and persist the derived fields."""
        deductions_dict = {"80C": self.declared_deductions} if self.declared_deductions else {}
        optimization = agent.optimize_regime_matrix(self.gross_income, deductions_dict)
        self.expected_tax = optimization["new_regime"]["total_tax"]
        self.risk_score = agent.evaluate_compliance_risk(
            self.gross_income, self.declared_deductions, self.tax_paid)
        if not self.flagged:
            self.compliance_status = _base_status(self.tax_paid, self.expected_tax)
        self.recommended_regime = optimization["recommended_regime"]
        db.update_row("taxpayers", "user_id", self.user_id, {
            "expected_tax": self.expected_tax,
            "calculated_risk_score": self.risk_score,
            "compliance_status": self.compliance_status,
            "recommended_regime": self.recommended_regime,
        })
        audit.record_event("ASSESSMENT_RECOMPUTED", actor, self.user_id, {
            "expected_tax": self.expected_tax, "risk_score": self.risk_score,
            "recommended_regime": self.recommended_regime})
        return optimization


class Notice:
    @staticmethod
    def create(user_id: str, notice_type: str, content: str, amount_due: float,
               actor: str = "system", dispatched: str = "SENT") -> dict:
        row = db.insert_row("compliance_notices", {
            "user_id": user_id,
            "notice_type": notice_type.upper(),
            "amount_due": amount_due,
            "generated_content": content,
            "dispatched_status": dispatched,
        })
        audit.record_event("NOTICE_SENT", actor, user_id,
                           {"notice_type": notice_type.upper(), "amount_due": amount_due})
        return row

    @staticmethod
    def for_user(user_id: str) -> list[dict]:
        return [r for r in db.select_all("compliance_notices", order_by="notice_id")
                if str(r.get("user_id")) == str(user_id)]

    @staticmethod
    def all() -> list[dict]:
        return db.select_all("compliance_notices", order_by="notice_id")


# --- helpers -----------------------------------------------------------------

def _base_status(tax_paid: float, expected_tax: float) -> str:
    return get_compliance_status(tax_paid, expected_tax)


def _normalise_deductions(deductions) -> dict | float:
    if deductions is None:
        return 0.0
    if isinstance(deductions, (int, float)):
        return float(deductions)
    return deductions


def _deduction_total(deductions) -> float:
    if isinstance(deductions, dict):
        return float(sum(deductions.values()))
    return float(deductions or 0)


def _mask_pan(pan: str | None) -> str | None:
    if not pan:
        return None
    if len(pan) <= 5:
        return pan[:1] + "*" * (len(pan) - 1)
    return pan[:5]  # PAN like ABCDE1234F -> expose prefix only (type code), mask rest


# Backward-compatible alias so any older import keeps working.
User = Taxpayer
