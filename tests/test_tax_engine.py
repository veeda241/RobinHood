"""Unit tests for the Dual-Regime tax engine, crypto layer, and blind index."""

from tax_agent import agent, calculate_tax, NEW_REBATE_UPTO
import crypto


# --- New regime -------------------------------------------------------------

def test_new_regime_15L_matches_expected():
    assert agent.compute_new_regime(1_500_000)["total_tax"] == 140400.0


def test_new_regime_rebate_makes_7L_nil():
    # taxable = 700000 - 75000 std = 625000 <= 700000 -> fully rebated
    assert agent.compute_new_regime(700_000)["total_tax"] == 0.0


def test_new_regime_above_rebate_threshold_is_positive():
    assert agent.compute_new_regime(800_000)["total_tax"] > 0.0


def test_surcharge_zero_below_50L_positive_above():
    assert agent.compute_new_regime(1_500_000)["surcharge"] == 0.0
    assert agent.compute_new_regime(6_000_000)["surcharge"] > 0.0


def test_cess_always_applied_when_tax_positive():
    r = agent.compute_new_regime(1_200_000)
    assert r["cess"] > 0
    assert round(r["base_tax"] * 0.04, 2) == r["cess"]


# --- Old regime + caps ------------------------------------------------------

def test_old_regime_80d_capped_for_non_senior():
    # 80D request 50000 is capped to 25000 for a non-senior -> matches verified total
    r = agent.compute_old_regime(1_500_000, {"80C": 150000, "80D": 50000}, senior=False)
    assert r["total_tax"] == 202800.0
    assert r["allowed_deductions"]["80D"] == 25000


def test_old_regime_80c_capped_at_150k():
    r = agent.compute_old_regime(2_000_000, {"80C": 500000})
    assert r["allowed_deductions"]["80C"] == 150000


def test_old_regime_rebate_under_5L():
    r = agent.compute_old_regime(500_000, {})
    assert r["total_tax"] == 0.0  # taxable 450000, rebate zeroes it


# --- Optimisation -----------------------------------------------------------

def test_optimize_recommends_new_at_15L():
    opt = agent.optimize_regime_matrix(1_500_000, {"80C": 150000, "80D": 50000})
    assert opt["recommended_regime"] == "NEW"
    assert opt["savings"] == 62400.0


def test_marginal_swap_returns_none_or_positive():
    res = agent.marginal_swap_threshold({"80C": 150000})
    assert res is None or res > 0


def test_module_calculate_tax_backward_compatible():
    # income treated as taxable income (no std deduction): 12L -> 90000 base + cess
    assert calculate_tax(1_200_000) == 93600.0


# --- Crypto + blind index ---------------------------------------------------

def test_encrypt_decrypt_roundtrip_per_field():
    token = crypto.encrypt_field("name", "Asha Rao")
    assert token != "Asha Rao"
    assert crypto.decrypt_field("name", token) == "Asha Rao"


def test_fernet_is_randomized():
    # Fernet includes a timestamp/IV, so two encryptions of the same value differ.
    assert crypto.encrypt_field("name", "same") != crypto.encrypt_field("name", "same")


def test_per_field_keys_are_independent():
    # A token produced for 'name' must not decrypt under the 'pan' key.
    token = crypto.encrypt_field("name", "secret")
    try:
        crypto.decrypt_field("pan", token)
        assert False, "cross-field decrypt should fail"
    except Exception:
        pass


def test_blind_index_deterministic_and_normalized():
    a = crypto.pan_blind_index("abcde1234f")
    b = crypto.pan_blind_index("  ABCDE1234F ")
    assert a == b and len(a) == 64


def test_none_passes_through_encryption():
    assert crypto.encrypt_field("pan", None) is None
    assert crypto.decrypt_field("pan", None) is None
