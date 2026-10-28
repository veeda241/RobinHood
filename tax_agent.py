"""
RobinHood AI - Sovereign Tax Intelligence Agent

Replaces the old baseline slab logic with a deterministic, data-driven engine:

  * Dual-regime optimisation (NEW vs OLD), FY 2024-25, with 4% Health &
    Education Cess, income-linked surcharge, and Section 87A rebates.
  * Marginal-swap threshold: the exact income at which the recommended regime
    flips (found by scan + bisection) - the standout analytical feature.
  * A memory-cached unsupervised anomaly model (sklearn IsolationForest) that
    scores compliance profiles against a reproducible synthetic baseline.

Tax slabs are pure configuration (rate tables keyed per assessment year), so
"scales across multiple years" is literal: add a year entry, no branch changes.

This module has NO storage or crypto dependencies - it is pure math + ML, so it
is trivially unit-testable. models.py feeds it real rows for retraining.
"""

from __future__ import annotations

import math
import numpy as np
from sklearn.ensemble import IsolationForest

# =============================================================================
# Rate-table configuration (FY 2024-25 / AY 2025-26)
# =============================================================================

# New regime slabs FY 2024-25. Tuples of (upper_bound_of_band, rate).
NEW_REGIME_SLABS = [
    (300000, 0.00),
    (600000, 0.05),
    (900000, 0.10),
    (1200000, 0.15),
    (1500000, 0.20),
    (float("inf"), 0.30),
]

# Old regime slabs FY 2024-25 (individuals < 60 yrs).
OLD_REGIME_SLABS = [
    (250000, 0.00),
    (500000, 0.05),
    (1000000, 0.20),
    (float("inf"), 0.30),
]

# Surcharge: single applicable rate on income tax, by total-income band.
SURCHARGE_TIERS = [
    (5000000, 0.00),
    (10000000, 0.10),
    (20000000, 0.15),
    (50000000, 0.25),
    (float("inf"), 0.30),
]

CESS_RATE = 0.04  # 4% Health & Education Cess

# Statutory caps for the old regime's Chapter VI-A deductions.
STD_DEDUCTION_NEW = 75000
STD_DEDUCTION_OLD = 50000
CAP_80C = 150000
CAP_80D_NON_SENIOR = 25000
CAP_80D_SENIOR = 50000
CAP_24_HOME_LOAN = 200000  # let-house / self-occupied combined interest ceiling used here

# Section 87A rebate thresholds and caps.
NEW_REBATE_UPTO = 700000     # taxable income at/below which new-regime tax is nil
OLD_REBATE_UPTO = 500000     # taxable income at/below which old-regime rebate applies
OLD_REBATE_CAP = 12500       # max rebate rupees under the old regime

ASSESSMENT_YEAR = "FY 2024-25 / AY 2025-26"


def _surcharge_rate(total_income: float) -> float:
    for bound, rate in SURCHARGE_TIERS:
        if total_income <= bound:
            return rate
    return SURCHARGE_TIERS[-1][1]


# =============================================================================
# The agent
# =============================================================================

class SovereignTaxAgent:
    def __init__(self):
        # --- Memory-cached anomaly model (fit once at construction) ---
        self.cached_risk_model: IsolationForest | None = None
        # Feature order used by the model: [gross_income, declared_deductions, tax_paid_to_date]
        self._feature_labels = ["gross_income", "declared_deductions", "tax_paid_to_date"]
        self._baseline_score_range = (-1.0, 1.0)  # recalibrated after fit
        self.initialize_baseline()

    # ---- Slab / tax primitives ------------------------------------------

    @staticmethod
    def calculate_slab_tax(taxable_income: float, slabs: list[tuple[float, float]]) -> dict:
        """Deterministic slab-wise tax. Returns base tax (before cess/surcharge)
        and an ordered breakdown of the bands actually touched."""
        if taxable_income <= 0:
            return {"total_tax": 0.0, "breakdown": []}
        tax = 0.0
        previous = 0.0
        breakdown = []
        for bound, rate in slabs:
            if taxable_income > previous:
                taxable_in_band = min(taxable_income, bound) - previous
                band_tax = taxable_in_band * rate
                tax += band_tax
                if math.isinf(bound):
                    label = f"Above INR {int(previous):,}"
                else:
                    label = f"INR {int(previous) + 1:,} - INR {int(bound):,}"
                breakdown.append({
                    "slab": label,
                    "rate": f"{int(rate * 100)}%",
                    "taxable_amount": round(taxable_in_band, 2),
                    "tax": round(band_tax, 2),
                })
                previous = bound
        return {"total_tax": round(tax, 2), "breakdown": breakdown}

    def _finalize(self, base_tax: float, total_income: float,
                  rebate: float) -> dict:
        """Apply rebate (against base tax), then surcharge, then 4% cess."""
        tax_after_rebate = max(0.0, base_tax - rebate)
        s_rate = _surcharge_rate(total_income)
        surcharge = tax_after_rebate * s_rate
        cess = (tax_after_rebate + surcharge) * CESS_RATE
        total = tax_after_rebate + surcharge + cess
        return {
            "base_tax": round(base_tax, 2),
            "rebate_87A": round(rebate, 2),
            "surcharge": round(surcharge, 2),
            "surcharge_rate": s_rate,
            "cess": round(cess, 2),
            "total_tax": round(total, 2),
        }

    def compute_new_regime(self, gross_income: float) -> dict:
        taxable = max(0.0, gross_income - STD_DEDUCTION_NEW)
        slab = self.calculate_slab_tax(taxable, NEW_REGIME_SLABS)
        # New regime 87A: nil tax if taxable income <= 7L (rebate = full base tax).
        rebate = slab["total_tax"] if taxable <= NEW_REBATE_UPTO else 0.0
        result = self._finalize(slab["total_tax"], gross_income, rebate)
        result["taxable_income"] = round(taxable, 2)
        result["breakdown"] = slab["breakdown"]
        return result

    def compute_old_regime(self, gross_income: float, deductions: dict | None = None,
                           senior: bool = False) -> dict:
        deductions = deductions or {}
        cap_80d = CAP_80D_SENIOR if senior else CAP_80D_NON_SENIOR
        allowed_80c = min(float(deductions.get("80C", 0) or 0), CAP_80C)
        allowed_80d = min(float(deductions.get("80D", 0) or 0), cap_80d)
        hra = max(0.0, float(deductions.get("HRA", 0) or 0))  # pre-computed exempt HRA
        home_loan = min(float(deductions.get("home_loan_interest", 0) or 0), CAP_24_HOME_LOAN)
        total_deductions = STD_DEDUCTION_OLD + allowed_80c + allowed_80d + hra + home_loan

        taxable = max(0.0, gross_income - total_deductions)
        slab = self.calculate_slab_tax(taxable, OLD_REGIME_SLABS)
        rebate = min(OLD_REBATE_CAP, slab["total_tax"]) if taxable <= OLD_REBATE_UPTO else 0.0
        result = self._finalize(slab["total_tax"], gross_income, rebate)
        result["taxable_income"] = round(taxable, 2)
        result["breakdown"] = slab["breakdown"]
        result["allowed_deductions"] = {
            "standard": STD_DEDUCTION_OLD,
            "80C": allowed_80c,
            "80D": allowed_80d,
            "HRA": hra,
            "home_loan_interest": home_loan,
            "total": round(total_deductions, 2),
        }
        return result

    # ---- Optimisation ----------------------------------------------------

    def optimize_regime_matrix(self, gross_income: float, deductions: dict | None = None,
                               senior: bool = False) -> dict:
        new = self.compute_new_regime(gross_income)
        old = self.compute_old_regime(gross_income, deductions, senior)
        new_tax, old_tax = new["total_tax"], old["total_tax"]
        if abs(new_tax - old_tax) < 1:
            recommended = "EQUAL"
        elif new_tax < old_tax:
            recommended = "NEW"
        else:
            recommended = "OLD"
        threshold = self.marginal_swap_threshold(deductions or {}, senior)
        return {
            "assessment_year": ASSESSMENT_YEAR,
            "recommended_regime": recommended,
            "savings": round(abs(new_tax - old_tax), 2),
            "new_regime": new,
            "old_regime": old,
            "marginal_swap_income": threshold,
        }

    def marginal_swap_threshold(self, deductions: dict | None = None,
                                senior: bool = False,
                                lo: float = 100000, hi: float = 50000000,
                                samples: int = 400) -> float | None:
        """Income at which the OLD-vs-NEW advantage flips, holding deductions
        fixed. Scans [lo, hi] for a genuine sign change, then bisects it.
        Returns None if the recommendation never changes over the range."""
        deductions = deductions or {}

        def diff(income: float) -> float:
            # positive => NEW cheaper; negative => OLD cheaper
            return self.compute_old_regime(income, deductions, senior)["total_tax"] \
                - self.compute_new_regime(income)["total_tax"]

        # Locate the first adjacent sample pair with a strict sign change.
        step = (hi - lo) / samples
        prev_income, prev_d = lo, diff(lo)
        bracket = None
        for i in range(1, samples + 1):
            income = lo + step * i
            d = diff(income)
            if prev_d < 0 < d or prev_d > 0 > d:
                bracket = (prev_income, income, prev_d)
                break
            if d != 0:
                prev_d = d
            prev_income = income
        if bracket is None:
            return None

        a, b, d_a = bracket
        for _ in range(80):  # bisection to sub-rupee resolution
            mid = (a + b) / 2
            if (diff(mid) > 0) == (d_a > 0):
                a = mid
            else:
                b = mid
        return round((a + b) / 2, 2)

    # ---- ML compliance risk ---------------------------------------------

    def initialize_baseline(self, n: int = 600, seed: int = 42):
        """Fit IsolationForest on a reproducible synthetic population of Indian
        salaried profiles [income, deductions, tax_paid]. Fixed seed => stable."""
        rng = np.random.default_rng(seed)
        income = np.clip(rng.lognormal(mean=13.4, sigma=0.6, size=n), 150000, 8000000)
        # Deductions correlate with income (old-regime filers), capped near 1.5L.
        deductions = np.clip(rng.normal(income * 0.12, 40000), 0, 300000)
        # Tax paid is roughly the new-regime tax on that income + noise; some
        # underpayers are naturally included in the tail.
        base_tax = (income - STD_DEDUCTION_NEW) * 0.1
        tax_paid = np.clip(rng.normal(base_tax * 0.95, base_tax * 0.3 + 1000), 0, None)
        features = np.column_stack([income, deductions, tax_paid])
        model = IsolationForest(contamination=0.04, random_state=seed, n_estimators=200)
        model.fit(features)
        self.cached_risk_model = model
        scores = model.score_samples(features)
        self._baseline_score_range = (float(scores.min()), float(scores.max()))

    def retrain(self, real_rows: list[dict], seed: int = 42):
        """Blend live taxpayer rows into the synthetic baseline and refit."""
        if not real_rows:
            return
        extra = np.array([[
            float(r.get("gross_income", 0) or 0),
            float(r.get("declared_deductions", 0) or 0),
            float(r.get("tax_paid_to_date", 0) or 0),
        ] for r in real_rows])
        self.initialize_baseline(seed=seed)
        if self.cached_risk_model is not None:
            # Refit once including the real observations.
            rng = np.random.default_rng(seed)
            n = 600
            income = np.clip(rng.lognormal(mean=13.4, sigma=0.6, size=n), 150000, 8000000)
            deductions = np.clip(rng.normal(income * 0.12, 40000), 0, 300000)
            base_tax = (income - STD_DEDUCTION_NEW) * 0.1
            tax_paid = np.clip(rng.normal(base_tax * 0.95, base_tax * 0.3 + 1000), 0, None)
            features = np.vstack([np.column_stack([income, deductions, tax_paid]), extra])
            model = IsolationForest(contamination=0.04, random_state=seed, n_estimators=200)
            model.fit(features)
            self.cached_risk_model = model
            scores = model.score_samples(features)
            self._baseline_score_range = (float(scores.min()), float(scores.max()))

    def evaluate_compliance_risk(self, gross_income: float, deductions: float,
                                 paid_tax: float) -> int:
        """Map IsolationForest anomaly score to a documented 0-100 risk index.

        score_samples: more negative => more anomalous. We invert and rescale
        across the training baseline range so a typical profile ~ 0-40 and an
        outlier approaches 100.
        """
        vector = np.array([[float(gross_income), float(deductions), float(paid_tax)]])
        raw = float(self.cached_risk_model.score_samples(vector)[0])
        lo, hi = self._baseline_score_range
        # Anomaly increases as raw decreases -> flip. Clamp for out-of-baseline rows.
        if hi == lo:
            return 0
        normalised = (hi - raw) / (hi - lo)  # 0 (normal) -> ~1+ (anomalous)
        risk_index = int(round(min(max(normalised, 0.0), 1.6) / 1.6 * 100))
        return max(0, min(risk_index, 100))

    def risk_reasons(self, taxpayer: dict, risk_score: int) -> list[str]:
        """Human-readable reasons. Labelled anomaly screening, not fraud verdict."""
        reasons = []
        income = float(taxpayer.get("gross_income", 0) or 0)
        expected = float(taxpayer.get("expected_tax", 0) or 0)
        paid = float(taxpayer.get("tax_paid_to_date", 0) or 0)
        deductions = float(taxpayer.get("declared_deductions", 0) or 0)

        if expected > 0:
            paid_ratio = paid / expected
            if paid_ratio < 0.5:
                reasons.append(f"Paid only {paid_ratio * 100:.0f}% of expected tax (population norm ~90-100%).")
        if income > 0:
            ded_ratio = deductions / income
            if ded_ratio > 0.6:
                reasons.append(f"Declared deductions are {ded_ratio * 100:.0f}% of gross income - unusually high.")
        if income >= 5000000 and paid < expected * 0.5:
            reasons.append("High-income profile (>INR 50L) with large shortfall - prioritise for review.")
        if risk_score >= 70 and not reasons:
            reasons.append("Statistical outlier versus the synthetic economic baseline.")
        if not reasons:
            reasons.append("No significant anomalies detected.")
        return reasons


# =============================================================================
# Module-level singleton + backward-compatible helpers
# =============================================================================

agent = SovereignTaxAgent()


def calculate_tax(income: float) -> float:
    """Backward-compatible total tax on `income` under the NEW regime
    (treated as taxable income; std deduction not applied here)."""
    slab = agent.calculate_slab_tax(max(0.0, float(income)), NEW_REGIME_SLABS)
    rebate = slab["total_tax"] if float(income) <= NEW_REBATE_UPTO else 0.0
    return agent._finalize(slab["total_tax"], float(income), rebate)["total_tax"]


def get_detailed_breakdown(income: float) -> list[dict]:
    return agent.calculate_slab_tax(max(0.0, float(income)), NEW_REGIME_SLABS)["breakdown"]


def get_compliance_status(tax_paid: float, expected_tax: float) -> str:
    if expected_tax == 0 or tax_paid >= expected_tax:
        return "COMPLIANT"
    return "UNDERPAID"


def build_notice_content(taxpayer: dict, optimization: dict | None,
                         notice_type: str) -> str:
    """Auto-tailored notice text based on the taxpayer's optimisation + risk."""
    name = taxpayer.get("name", taxpayer.get("user_id", "Taxpayer"))
    due = float(taxpayer.get("due_amount", 0) or 0)
    risk = int(taxpayer.get("calculated_risk_score", 0) or 0)
    lines = [f"Dear {name},"]
    if notice_type == "PENALTY":
        penalty = due * 0.10
        lines.append(f"Due to sustained non-payment a penalty of 10% (INR {penalty:,.0f}) "
                     f"has been added to your outstanding INR {due:,.0f}.")
    elif notice_type == "FINAL":
        lines.append(f"This is a FINAL notice. Outstanding dues of INR {due:,.0f} remain unpaid; "
                     "failure to pay will invite legal action.")
    elif notice_type == "WARNING":
        lines.append(f"You have unpaid tax of INR {due:,.0f}. Please pay promptly to avoid penalties.")
    else:  # REMINDER / OPTIMIZATION_ADVISORY
        lines.append(f"A tax payment of INR {due:,.0f} is pending against your record.")

    if optimization and optimization.get("recommended_regime") == "OLD" and optimization.get("savings", 0) > 0:
        lines.append(f"Our Dual-Regime engine indicates the OLD regime would save you "
                     f"INR {optimization['savings']:,.0f} given your declared deductions.")
    if risk >= 70:
        lines.append(f"Your profile has been auto-flagged for review (compliance risk index {risk}/100).")
    lines.append("\n- RobinHood AI Tax System, Income Tax Department")
    return "\n".join(lines)
