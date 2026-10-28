"""
RobinHood AI - Flask API Gateway & Core Application Routers

Three-tier, privacy-preserving architecture:
  * VISUAL layer  -> React SPA served from frontend/dist (catch-all below)
  * INTELLIGENT   -> these routers wrap the SovereignTaxAgent + risk engine
  * SECURE DATA   -> Supabase (encrypted PII columns + chained audit ledger)

Security posture: authentication on every state-changing route, hardened CORS,
rate limiting, input validation, safe error responses that never leak internals,
and a tamper-evident audit trail written through models -> audit.
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, g, session
from flask_cors import CORS

load_dotenv()

import db
import audit
import validation
from tax_agent import agent, get_detailed_breakdown, calculate_tax, build_notice_content, ASSESSMENT_YEAR
from models import Taxpayer, Notice
from auth_decorators import require_supabase_auth, require_role
from admin_auth import auth_bp
from http_security import limiter

DEBUG = os.getenv("FLASK_ENV", "production").lower() != "production"
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:8080")

# static_url_path=None disables Flask's built-in /<path:filename> static route,
# which would otherwise shadow the SPA catch-all and 404 deep links like /admin.
app = Flask(__name__, static_folder=None)
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
app.config["SECRET_KEY"] = os.getenv("SESSION_SECRET") or os.urandom(32).hex()
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# CORS restricted to the single known frontend origin (not wide-open).
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGIN}}, supports_credentials=True)

limiter.init_app(app)
app.register_blueprint(auth_bp)


# --- Static SPA serving (visual layer) --------------------------------------

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if not os.path.isdir(DIST_DIR):
        return jsonify({"error": "Frontend build not found. Run `npm run build` in frontend/."}), 503
    if path and os.path.exists(os.path.join(DIST_DIR, path)):
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, "index.html")


# --- Error handling: never leak internals -----------------------------------

@app.errorhandler(db.StorageError)
def _storage_error(err):
    return jsonify({"error": "A storage error occurred."}), 502


@app.errorhandler(Exception)
def _unhandled(err):
    # Let real HTTP exceptions (incl. 401/403/429 from auth + rate limiter)
    # render normally; only swallow unexpected errors without leaking internals.
    from werkzeug.exceptions import HTTPException
    if isinstance(err, HTTPException):
        return jsonify({"error": err.name}), err.code
    app.logger.exception("Unhandled error")
    return jsonify({"error": "Internal server error."}), 500


# --- Tax intelligence (public, read-only, powers the sliders) ---------------

@app.route("/api/tax/calculate", methods=["POST"])
def calculate_tax_route():
    data = request.get_json(silent=True) or {}
    err = validation.require_fields(data, "income")
    if err:
        return jsonify({"error": err}), 400
    income, verr = validation.as_nonneg_number(data["income"], "income")
    if verr:
        return jsonify({"error": verr}), 400
    return jsonify({"tax": calculate_tax(income), "breakdown": get_detailed_breakdown(income)})


@app.route("/api/tax/optimize", methods=["POST"])
def optimize_route():
    """Deterministic Dual-Regime preview. No DB write, no auth - used live by
    the citizen slider UI."""
    data = request.get_json(silent=True) or {}
    income, err = validation.as_nonneg_number(data.get("gross_income"), "gross_income")
    if err:
        return jsonify({"error": err}), 400
    ded_raw = data.get("deductions", {}) or {}
    if not isinstance(ded_raw, dict):
        return jsonify({"error": "'deductions' must be an object."}), 400
    deductions = {}
    for key in ("80C", "80D", "HRA", "home_loan_interest"):
        if key in ded_raw:
            val, derr = validation.as_nonneg_number(ded_raw[key], key)
            if derr:
                return jsonify({"error": derr}), 400
            deductions[key] = val
    senior = bool(data.get("senior", False))
    return jsonify(agent.optimize_regime_matrix(income, deductions, senior))


@app.route("/api/tax/curve", methods=["GET"])
def curve_route():
    """Old-vs-new tax curve over an income grid + the crossover threshold.
    Powers the frontend AreaChart; pure computation, no DB, no auth."""
    income_max, err = validation.as_nonneg_number(request.args.get("income_max", 5000000), "income_max")
    if err:
        return jsonify({"error": err}), 400
    income_max = max(500000, min(income_max, 100000000))
    deductions = {}
    for key in ("80C", "80D", "HRA", "home_loan_interest"):
        val, derr = validation.as_nonneg_number(request.args.get(key, 0), key)
        if derr:
            return jsonify({"error": derr}), 400
        deductions[key] = val
    senior = request.args.get("senior", "0") in ("1", "true", "yes")
    points = 60
    step = income_max / points
    grid = []
    for i in range(1, points + 1):
        inc = i * step
        new_tax = agent.compute_new_regime(inc)["total_tax"]
        old_tax = agent.compute_old_regime(inc, deductions, senior)["total_tax"]
        grid.append({
            "income": round(inc, 0),
            "new_tax": round(new_tax, 0),
            "old_tax": round(old_tax, 0),
            "recommended": "NEW" if new_tax <= old_tax else "OLD",
        })
    return jsonify({
        "assessment_year": ASSESSMENT_YEAR,
        "points": grid,
        "marginal_swap_income": agent.marginal_swap_threshold(deductions, senior),
    })


@app.route("/api/regulations", methods=["GET"])
def regulations_route():
    """Honest, statute-derived feed (FY 2024-25 constants from the engine).
    Replaces the deleted US mock array - every item is a real rule."""
    return jsonify([
        {"id": "slabs-new", "title": "New Regime Slabs (FY 2024-25)",
         "description": "Nil up to \u20b93L, then 5/10/15/20/30% across the \u20b93L-\u20b915L bands; \u20b975,000 standard deduction.",
         "source": "Finance Act 2024 \u00b7 \u00a7115BAC", "category": "income"},
        {"id": "rebate-7l", "title": "Section 87A: Tax-Free up to \u20b97 Lakh",
         "description": "Full rebate for taxable income up to \u20b97L under the new regime (\u20b95L / \u20b912,500 rebate under the old regime).",
         "source": "Income Tax Act \u00b7 \u00a787A", "category": "income"},
        {"id": "ded-cap", "title": "Chapter VI-A Deduction Caps",
         "description": "80C capped at \u20b91.5L; 80D at \u20b925k (\u20b950k for senior citizens); \u00a724(b) home-loan interest at \u20b92L (old regime).",
         "source": "Income Tax Act \u00b7 \u00a780C/\u00a780D/\u00a724", "category": "income"},
        {"id": "cess-surcharge", "title": "Cess & Surcharge Apply to Both Regimes",
         "description": "4% Health & Education Cess; surcharge 10-37% on base tax above \u20b950L (new regime caps surcharge at 30%).",
         "source": "Finance Act 2024", "category": "other"},
    ])


# --- Consolidated assess gateway (persist + ML risk + encrypt + audit) ------

@app.route("/api/tax/assess", methods=["POST"])
@require_supabase_auth
@limiter.limit("30 per minute")
def assess_route():
    data = request.get_json(silent=True) or {}
    err = validation.require_fields(data, "gross_income")
    if err:
        return jsonify({"error": err}), 400
    income, err = validation.as_nonneg_number(data["gross_income"], "gross_income")
    if err:
        return jsonify({"error": err}), 400
    name, err = validation.as_length_limited(data.get("name", data.get("user_id", "Citizen")), "name", 120)
    if err:
        return jsonify({"error": err}), 400
    paid, err = validation.as_nonneg_number(data.get("tax_paid", 0), "tax_paid")
    if err:
        return jsonify({"error": err}), 400
    deductions = data.get("deductions", {}) or {}

    actor_id = getattr(g.current_user, "id", "api")
    taxpayer = Taxpayer.create(
        name=name, gross_income=income, tax_paid=paid, deductions=deductions,
        pan=data.get("pan"), assets_value=data.get("assets_value"),
        user_id=data.get("user_id"), actor=actor_id,
    )
    optimization = taxpayer.recompute_assessment(actor=actor_id)
    risk = agent.evaluate_compliance_risk(income, taxpayer.declared_deductions, paid)
    reasons = agent.risk_reasons({
        "gross_income": income, "declared_deductions": taxpayer.declared_deductions,
        "tax_paid_to_date": paid, "expected_tax": taxpayer.expected_tax,
    }, risk)
    return jsonify({
        "status": "SUCCESS",
        "taxpayer_id": taxpayer.user_id,
        "assessment": {
            "recommended_regime": optimization["recommended_regime"],
            "savings": optimization["savings"],
            "risk_index": risk,
            "risk_reasons": reasons,
            "compliance_status": taxpayer.compliance_status,
        },
        "optimization": optimization,
    }), 201


# --- Admin: taxpayer registry, flags, payments, stats -----------------------

@app.route("/api/users", methods=["GET"])
@require_role("admin")
def get_users():
    return jsonify([u.to_dict() for u in Taxpayer.get_all()])


@app.route("/api/users", methods=["POST"])
@require_role("admin")
@limiter.limit("30 per minute")
def add_user():
    data = request.get_json(silent=True) or {}
    err = validation.require_fields(data, "user_id", "declared_income")
    if err:
        return jsonify({"error": err}), 400
    income, verr = validation.as_nonneg_number(data["declared_income"], "declared_income")
    if verr:
        return jsonify({"error": verr}), 400
    paid, verr = validation.as_nonneg_number(data.get("tax_paid", 0), "tax_paid")
    if verr:
        return jsonify({"error": verr}), 400
    tp = Taxpayer.create(
        name=data.get("name", data["user_id"]), gross_income=income, tax_paid=paid,
        deductions=data.get("deductions", 0), user_id=data["user_id"],
        pan=data.get("pan"), assets_value=data.get("assets_value"),
        actor=f"admin:{request.headers.get('X-Actor', 'admin')}",
    )
    return jsonify({"message": "Taxpayer added.", "user": tp.to_dict()}), 201


@app.route("/api/users/flag/<user_id>", methods=["PUT"])
@require_role("admin")
def flag_user(user_id):
    tp = Taxpayer.toggle_flag(user_id, actor=session_actor())
    if not tp:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"message": f"Flag updated for {user_id}.", "flagged": tp.flagged})


@app.route("/api/payments/process", methods=["POST"])
@require_role("admin")
def process_payment_route():
    data = request.get_json(silent=True) or {}
    err = validation.require_fields(data, "user_id", "amount")
    if err:
        return jsonify({"error": err}), 400
    amount, verr = validation.as_nonneg_number(data["amount"], "amount")
    if verr:
        return jsonify({"error": verr}), 400
    tp = Taxpayer.record_payment(data["user_id"], amount, actor=session_actor())
    if not tp:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"message": "Payment recorded.", "user": tp.to_dict()})


@app.route("/api/notices/send/<user_id>", methods=["POST"])
@require_role("admin")
def send_notice_route(user_id):
    data = request.get_json(silent=True) or {}
    notice_type = str(data.get("type", "reminder")).lower()
    if notice_type not in ("reminder", "warning", "final", "penalty"):
        return jsonify({"error": "Invalid notice type."}), 400
    tp = Taxpayer.get_by_id(user_id)
    if not tp:
        return jsonify({"error": "User not found."}), 404
    optimization = tp.recompute_assessment(actor=session_actor())
    content = build_notice_content(tp.to_dict(), optimization, notice_type.upper())
    row = Notice.create(user_id, notice_type, content, tp.due_amount, actor=session_actor())
    return jsonify({"message": f"{notice_type.title()} notice sent.", "notice": row})


@app.route("/api/notices/<user_id>", methods=["GET"])
@require_role("admin")
def notice_history(user_id):
    return jsonify(Notice.for_user(user_id))


@app.route("/api/stats", methods=["GET"])
@require_role("admin")
def get_stats():
    users = Taxpayer.get_all()
    total_expected = sum(u.expected_tax for u in users)
    total_paid = sum(u.tax_paid for u in users)
    return jsonify({
        "total": len(users),
        "compliant": sum(1 for u in users if u.compliance_status == "COMPLIANT"),
        "underpaid": sum(1 for u in users if u.compliance_status == "UNDERPAID"),
        "flagged": sum(1 for u in users if u.flagged),
        "high_risk": sum(1 for u in users if u.risk_score >= 70),
        "total_expected": total_expected,
        "total_paid": total_paid,
        "total_due": sum(u.due_amount for u in users),
        "collection_rate": round((total_paid / total_expected * 100) if total_expected else 100, 1),
    })


@app.route("/api/risk", methods=["GET"])
@require_role("admin")
def risk_feed():
    """Real AI insights for the dashboard: risk score + human-readable reasons."""
    out = []
    for u in Taxpayer.get_all():
        reasons = agent.risk_reasons({
            "gross_income": u.gross_income, "declared_deductions": u.declared_deductions,
            "tax_paid_to_date": u.tax_paid, "expected_tax": u.expected_tax,
        }, u.risk_score)
        out.append({
            "user_id": u.user_id, "name": u.name, "risk_score": u.risk_score,
            "gross_income": u.gross_income, "paid_ratio": round(
                (u.tax_paid / u.expected_tax) if u.expected_tax else 1.0, 2),
            "reasons": reasons,
        })
    return jsonify(sorted(out, key=lambda r: r["risk_score"], reverse=True))


@app.route("/api/trends", methods=["GET"])
@require_role("admin")
def trends():
    """DB-backed collection vs dues by income band (replaces the US mock chart)."""
    bands = [
        ("Under 5L", 0, 500000), ("5-10L", 500000, 1000000), ("10-15L", 1000000, 1500000),
        ("15-25L", 1500000, 2500000), ("Above 25L", 2500000, float("inf")),
    ]
    users = Taxpayer.get_all()
    data = []
    for label, lo, hi in bands:
        bucket = [u for u in users if lo <= u.gross_income < hi]
        data.append({
            "band": label,
            "expected": round(sum(u.expected_tax for u in bucket), 0),
            "collected": round(sum(u.tax_paid for u in bucket), 0),
            "count": len(bucket),
        })
    return jsonify(data)


@app.route("/api/audit/verify", methods=["GET"])
@require_role("admin")
def audit_verify():
    return jsonify(audit.verify_chain())


@app.route("/api/audit/trail", methods=["GET"])
@require_role("admin")
def audit_trail():
    limit = validation.clamp_int(request.args.get("limit", 50), 1, 500)
    return jsonify(audit.get_trail(limit))


# --- helpers ----------------------------------------------------------------

def session_actor():
    return session.get("actor", "admin")


if __name__ == "__main__":
    # In offline demo mode, seed a small taxpayer registry so the dashboard is
    # populated without a live Supabase project.
    if db.demo_mode():
        from setup_db import seed_demo_store
        seed_demo_store()
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
