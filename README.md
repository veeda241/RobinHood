# RobinHood AI - Privacy-Preserving Tax Intelligence

![RobinHood AI](https://img.shields.io/badge/RobinHood-AI%20Tax%20System-667eea?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-38ef7d?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-f45c43?style=for-the-badge&logo=flask&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

A three-tier, intelligent & privacy-preserving tax compliance system for India's
dual-regime (FY 2024-25) framework:

```
VISUAL LAYER     React + Shadcn SPA  ->  citizen optimizer & admin command center
INTELLIGENT      Flask gateway       ->  SovereignTaxAgent (dual-regime optimizer,
                                         marginal-swap threshold, IsolationForest risk)
SECURE DATA      Supabase            ->  field-level Fernet encryption (HKDF-derived
                                         per-field keys), blind-index PAN lookup,
                                         chained tamper-evident audit ledger, RLS
```

## 🔐 Security posture

- **Hybrid auth** - Supabase JWT (Bearer) for citizen/API traffic on `/api/tax/assess`;
  signed Flask session cookie (PBKDF2-verified, rate-limited 5/min) for the admin
  dashboard and CLI-facing routes.
- **Encryption at the application layer** - names, PANs and asset values are stored
  as Fernet ciphertext with a *distinct key per column* (`HKDF(master, field)`), so
  one leaked key never exposes the whole table. PAN search works via a deterministic
  HMAC blind index, never by decrypting.
- **Tamper-evident audit ledger** - every mutating action appends a row whose
  `payload_hash = SHA256(prev_hash | timestamp | action | actor | target | payload)`.
  Rows survive subject deletion (no FK/CASCADE) and the table is append-only at the
  DB level. `verify_chain()` (dashboard button, `/api/audit/verify`, or `python robinhood_cli.py audit verify`)
  pinpoints the exact `log_id` where a chain was broken.
- **Real RLS** - citizens can only select their own `taxpayers` row; the ledger and
  notices are service-role only. No blanket `USING (true)` policies.
- **Hardened gateway** - CORS pinned to the frontend origin, rate limiting, input
  validation with clean 400s, and error responses that never leak internals.

### ⚠️ Discovered & remediated risk (disclosed deliberately)
Earlier revisions of this project committed a **hardcoded MySQL root password** in
`db.py`. Because it lived in git history it must be treated as public: the MySQL
credential was **rotated out of existence** when the data layer migrated fully to
Supabase (the driver, `setup_database.sql` and local SQL were deleted, and secrets
now come from a gitignored `.env`). If you forked the repo before this migration,
rotate any password that matches the old value.

## 🚀 Quick Start

### 1. Configure secrets
```bash
cp .env.example .env        # fill in Supabase URL, service-role key, CRYPTO_KEY...
```
Generate the Fernet master key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
**Never put `SUPABASE_SERVICE_ROLE_KEY` in `frontend/.env`** - the frontend only
takes the anon key (`frontend/.env.example`).

Leave `SUPABASE_URL` empty to run in **offline demo mode**: an in-memory store
mirrors the Supabase tables, eight demo taxpayers are seeded, and the full
pipeline (encrypt -> optimize -> risk -> ledger) stays demonstrable without network.

### 2. Apply the schema (real Supabase project)
Open the Supabase SQL Editor and run [`supabase_schema.sql`](supabase_schema.sql)
once. Seed demo taxpayers with `python setup_db.py`.

### 3. Backend
```bash
pip install -r requirements.txt
python app.py               # http://localhost:5000 (debug off unless FLASK_ENV != production)
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev                 # http://localhost:8080, proxies /api -> :5000
# or for production serving from Flask:
npm run build
```

**Offline demo admin login:** `admin@robinhood.gov.in` / `admin-demo-123`
(the fallback used only when `ADMIN_PASSWORD_HASH` is unset - set it for anything real).

## 🧠 Intelligence engine

- Dual-regime math with 4% cess, surcharge tiers (10/15/25/30%), Section 87A
  rebates (₹7L nil-new / ₹5L+₹12.5k-old), ₹75k/₹50k standard deductions and
  Chapter VI-A caps (80C ₹1.5L, 80D ₹25k/₹50k senior, §24(b) ₹2L).
- `optimize_regime_matrix()` recommends NEW/OLD with savings;
  `marginal_swap_threshold()` bisects the exact income where the recommendation
  flips - drawn as the crossover marker on the portal chart.
- `IsolationForest(contamination=0.04)` over a fixed-seed synthetic baseline
  blended with real rows; `score_samples` is linearly mapped to a documented
  0-100 risk index. Labelled honestly: **anomaly screening**, not fraud detection.

## 🖥️ Frontend routes

| Route | Who | What |
|-------|-----|------|
| `/` | Citizen | Dual-Regime Tax Optimizer (sliders, debounced `/api/tax/optimize`, crossover `AreaChart`), quick estimator, statutory reference feed |
| `/login` | Admin | Rate-limited PBKDF2 login -> signed session cookie |
| `/admin` | Admin | Session-gated command center: stats, encrypted registry, ML Risk Matrix (scatter), Audit Ledger with Verify Integrity, real risk insights, collection trends |

## 📁 Project structure

```
RobinHood/
├── app.py               # Flask gateway (routes + hardening)
├── admin_auth.py        # PBKDF2 admin sessions (/api/admin/*, /api/auth/me)
├── auth_decorators.py   # @require_supabase_auth / @require_role
├── tax_agent.py         # SovereignTaxAgent: regimes + ML risk engine
├── crypto.py            # per-field Fernet + PAN blind index
├── audit.py             # chained ledger: record_event / verify_chain
├── db.py                # Supabase client + error wrapper + demo fallback
├── models.py            # Taxpayer/Notice over Supabase tables
├── validation.py        # input hygiene -> clean 400s
├── setup_db.py          # Supabase/demo seeder
├── supabase_schema.sql  # tables, RLS, append-only triggers
├── robinhood_cli.py     # optimize|risk|audit verify|audit trail|batch|model|admin
└── frontend/            # React 18 + Vite + TS + Shadcn + Supabase-js
```

## 🔧 API endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/tax/calculate` | POST | public | Single-regime estimate + breakdown |
| `/api/tax/optimize` | POST | public | Dual-regime matrix + savings + swap threshold |
| `/api/tax/curve` | GET | public | Old-vs-new curve + crossover for the chart |
| `/api/regulations` | GET | public | Statute-derived FY 2024-25 reference feed |
| `/api/tax/assess` | POST | Supabase JWT | Gateway: optimize -> risk -> encrypt -> insert -> ledger |
| `/api/admin/login` | POST | rate-limited | Admin session (PBKDF2) |
| `/api/auth/me` | GET | - | Current principal `{mode, role}` |
| `/api/users` (+`/flag/<id>`) | GET/POST/PUT | admin | Encrypted taxpayer registry |
| `/api/payments/process` | POST | admin | Record payment, recompute compliance |
| `/api/notices/send/<id>`, `/api/notices/<id>` | POST/GET | admin | Persisted tailored notices |
| `/api/stats`, `/api/risk`, `/api/trends` | GET | admin | Aggregates + live ML insights |
| `/api/audit/verify`, `/api/audit/trail` | GET | admin | Chain verification + ledger rows |

## 🧪 Tests

```bash
python -m pytest tests -q
```
Covers cess/surcharge/rebate edge cases, crossover monotonicity, encrypt round-trip
+ blind-index determinism, ledger tampering (5 chained events, then edit a row and
watch `verify_chain` name the exact `log_id`), JWT/session 401/403 paths and the
login rate limit.

## 📜 License

MIT License - Feel free to use and modify!

---
Built with ❤️ by the RobinHood AI Team
