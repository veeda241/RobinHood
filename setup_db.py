"""
RobinHood AI - Database Seeder

Two modes, chosen automatically:
  * Supabase configured -> seeds the live `taxpayers` table through the model
    layer (so PII is encrypted and each insert is audit-logged). Run
    supabase_schema.sql in the Supabase SQL Editor first.
  * Supabase NOT configured (offline demo / CI) -> seeds the in-memory store so
    the dashboard and CLI are immediately usable.

Usage:  python setup_db.py [--reset]
"""

import sys

import db
from models import Taxpayer

# name, gross_income, tax_paid, deductions_total, pan, assets_value
SAMPLE = [
    ("Asha Rao",      500000,  10000, 150000, "ABCDE1234F", 1200000),
    ("Bilal Khan",    800000,  25000, 150000, "BCDEF2345G", 2100000),
    ("Chaya Nair",   1200000,  45000, 175000, "CDEFG3456H", 5400000),
    ("Deep Varma",   1500000,  90000, 200000, "DEFGH4567J", 8800000),
    ("Elena D'Souza",2000000, 100000, 150000, "EFGHI5678K", 15000000),
    ("Farid Sheikh",  350000,      0,  50000, "FGHIJ6789L", 400000),
    ("Gita Iyer",     950000,  55000, 150000, "GHIJK7890M", 3300000),
    ("Harun Meher",   600000,  15000, 100000, "HIJKL8901N", 900000),
]


def _seed():
    for i, (name, income, paid, ded, pan, assets) in enumerate(SAMPLE):
        user_id = f"TXP{i + 1:03d}"
        if Taxpayer.get_by_id(user_id):
            continue
        Taxpayer.create(
            name=name, gross_income=income, tax_paid=paid,
            deductions={"80C": min(ded, 150000)}, user_id=user_id,
            pan=pan, assets_value=assets, actor="seeder",
        )
        print(f"  seeded {user_id} ({name})")


def seed_demo_store():
    """Populate the in-memory offline demo store (idempotent)."""
    if not db.demo_mode():
        return
    if db.select_all("taxpayers"):
        return
    print("Offline demo mode detected (no Supabase) - seeding in-memory store.")
    _seed()


def seed_supabase(reset: bool = False):
    if reset:
        client = db.get_supabase_client()
        # Delete all rows via an always-true filter. Ledger is append-only at the
        # DB tier (UPDATE/DELETE blocked), so a full reset must be done in the
        # SQL Editor, not here; we only clear notices + taxpayers.
        client.table("compliance_notices").delete().neq("user_id", "").execute()
        client.table("taxpayers").delete().neq("user_id", "").execute()
        print("Cleared existing notices and taxpayers (ledger is append-only).")
    _seed()


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    print("=" * 54)
    print("RobinHood AI - Database Seeder")
    print("=" * 54)
    if db.demo_mode():
        seed_demo_store()
        print(f"\nIn-memory store now holds {len(db.select_all('taxpayers'))} taxpayers.")
        print("Set SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in .env to seed real Supabase.")
    else:
        seed_supabase(reset=reset)
        print(f"\nSupabase now holds {len(db.select_all('taxpayers'))} taxpayers.")
