#!/usr/bin/env python3
"""
RobinHood AI - Administration CLI

Delegates ALL tax math to tax_agent.py (no duplicated slab logic) and all data
access to models.py / audit.py, so the CLI and the web API can never drift.

New high-value admin commands:
  optimize  - Dual-Regime optimisation for an income + deductions
  risk      - ML compliance anomaly scoring for the whole registry
  audit verify / audit trail   - tamper-evident ledger operations
  batch remind-all             - persist reminder notices for all underpayers
  model retrain                - blend live rows into the anomaly baseline
  admin login-hash             - generate a PBKDF2 hash for ADMIN_PASSWORD_HASH
"""

import argparse
import sys
import os

if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from tabulate import tabulate

try:
    from colorama import init, Fore, Style
    init()
    CYAN, GREEN, YELLOW, RED, BOLD, ENDC = Fore.CYAN, Fore.GREEN, Fore.YELLOW, Fore.RED, Style.BRIGHT, Style.RESET_ALL
except ImportError:
    CYAN = GREEN = YELLOW = RED = BOLD = ENDC = ""


def fmt(amount):
    return f"Rs.{amount:,.0f}"


def print_header():
    print(f"\n{CYAN}{BOLD}{'=' * 60}\n   ROBINHOOD AI - TAX ADMIN CLI\n{'=' * 60}{ENDC}")


# --- math commands (delegate to the agent) ----------------------------------

def cmd_calculate(args):
    from tax_agent import agent
    r = agent.compute_new_regime(args.income)
    print(f"\n{GREEN}{BOLD}NEW-REGIME TAX{ENDC}  income {fmt(args.income)} -> {BOLD}{fmt(r['total_tax'])}{ENDC}")
    rows = [(b["slab"], b["rate"], fmt(b["taxable_amount"]), fmt(b["tax"])) for b in r["breakdown"]]
    print(tabulate(rows, headers=["Slab", "Rate", "Taxable", "Tax"], tablefmt="grid"))
    print(f"Cess: {fmt(r['cess'])} | Surcharge: {fmt(r['surcharge'])} | 87A rebate: {fmt(r['rebate_87A'])}\n")


def cmd_compare(args):
    from tax_agent import calculate_tax
    rows = []
    for income in args.incomes:
        tax = calculate_tax(income)
        rows.append([fmt(income), fmt(tax), f"{(tax / income * 100) if income else 0:.2f}%", fmt(income - tax)])
    print(tabulate(rows, headers=["Income", "Tax", "Eff. Rate", "Take Home"], tablefmt="grid"))
    print()


def cmd_optimize(args):
    from tax_agent import agent
    deductions = {"80C": args.c80c, "80D": args.c80d, "HRA": args.hra, "home_loan_interest": args.home_loan}
    opt = agent.optimize_regime_matrix(args.income, deductions, senior=args.senior)
    new, old = opt["new_regime"], opt["old_regime"]
    print(f"\n{GREEN}{BOLD}DUAL-REGIME OPTIMISATION{ENDC}  income {fmt(args.income)}")
    print(tabulate([
        ["NEW", fmt(new["total_tax"]), fmt(new["taxable_income"])],
        ["OLD", fmt(old["total_tax"]), fmt(old["taxable_income"])],
    ], headers=["Regime", "Total Tax", "Taxable Income"], tablefmt="grid"))
    swap = opt["marginal_swap_income"]
    print(f"\nRecommended: {CYAN}{BOLD}{opt['recommended_regime']}{ENDC} | Savings: {fmt(opt['savings'])}")
    print(f"Marginal-swap income: {fmt(swap) if swap else 'No crossover for these deductions'}\n")


def cmd_slabs(args):
    from tax_agent import NEW_REGIME_SLABS, OLD_REGIME_SLABS, ASSESSMENT_YEAR
    print(f"\n{GREEN}{BOLD}TAX SLABS - {ASSESSMENT_YEAR}{ENDC}")
    for label, slabs in (("NEW REGIME", NEW_REGIME_SLABS), ("OLD REGIME", OLD_REGIME_SLABS)):
        print(f"\n{CYAN}{label}{ENDC}")
        rows, prev = [], 0.0
        for bound, rate in slabs:
            band = f"Above {fmt(prev)}" if bound == float('inf') else f"{fmt(prev + 1)} - {fmt(bound)}"
            rows.append([band, f"{int(rate * 100)}%"])
            prev = bound
        print(tabulate(rows, headers=["Income Range", "Rate"], tablefmt="grid"))
    print("\nBoth regimes: +4% Health & Education Cess; surcharge above INR 50L.\n")


# --- registry / compliance commands -----------------------------------------

def cmd_users(args):
    from models import Taxpayer
    try:
        users = Taxpayer.get_all()
    except Exception as e:
        print(f"{RED}DB error: {e}{ENDC}")
        return
    rows = [[f"{u.user_id}{' [FLAG]' if u.flagged else ''}", u.name, fmt(u.gross_income),
             fmt(u.expected_tax), fmt(u.tax_paid), fmt(u.due_amount), u.compliance_status, u.risk_score]
            for u in users]
    print(tabulate(rows, headers=["ID", "Name", "Income", "Expected", "Paid", "Due", "Status", "Risk"], tablefmt="grid"))
    print()


def cmd_add(args):
    from models import Taxpayer
    tp = Taxpayer.create(name=args.name or args.user_id, gross_income=args.income, tax_paid=args.paid or 0,
                        user_id=args.user_id, pan=args.pan, actor="cli-admin")
    print(f"{GREEN}Added {tp.user_id}: expected {fmt(tp.expected_tax)}, status {tp.compliance_status}{ENDC}\n")


def cmd_pay(args):
    from models import Taxpayer
    tp = Taxpayer.record_payment(args.user_id, args.amount, actor="cli-admin")
    print(f"{GREEN}Payment recorded. {args.user_id} now paid {fmt(tp.tax_paid)}, status {tp.compliance_status}{ENDC}\n"
          if tp else f"{RED}User not found{ENDC}\n")


def cmd_flag(args):
    from models import Taxpayer
    tp = Taxpayer.toggle_flag(args.user_id, actor="cli-admin")
    print(f"{YELLOW}Flag={'on' if tp.flagged else 'off'} for {args.user_id}{ENDC}\n" if tp else f"{RED}Not found{ENDC}\n")


def cmd_notice(args):
    from models import Taxpayer, Notice
    from tax_agent import build_notice_content
    tp = Taxpayer.get_by_id(args.user_id)
    if not tp:
        print(f"{RED}User not found{ENDC}\n")
        return
    opt = tp.recompute_assessment(actor="cli-admin")
    content = build_notice_content(tp.to_dict(), opt, args.type.upper())
    Notice.create(args.user_id, args.type, content, tp.due_amount, actor="cli-admin")
    print(f"{GREEN}{content}{ENDC}\n")


def cmd_remind_all(args):
    from models import Taxpayer, Notice
    from tax_agent import build_notice_content
    users = Taxpayer.get_all()
    targets = [u for u in users if u.compliance_status in ("UNDERPAID", "FLAGGED_FOR_REVIEW")]
    for u in targets:
        opt = u.recompute_assessment(actor="cli-batch")
        Notice.create(u.user_id, "reminder", build_notice_content(u.to_dict(), opt, "REMINDER"),
                      u.due_amount, actor="cli-batch")
    print(f"{GREEN}Sent {len(targets)} persisted reminders.{ENDC}\n")


def cmd_risk(args):
    from models import Taxpayer
    from tax_agent import agent
    rows = []
    for u in Taxpayer.get_all():
        reasons = agent.risk_reasons({"gross_income": u.gross_income, "declared_deductions": u.declared_deductions,
                                      "tax_paid_to_date": u.tax_paid, "expected_tax": u.expected_tax}, u.risk_score)
        rows.append([u.user_id, u.risk_score, ("ANOMALY" if u.risk_score >= 70 else "normal"), reasons[0]])
    print(tabulate(rows, headers=["ID", "Risk", "Class", "Top reason"], tablefmt="grid"))
    print()


def cmd_stats(args):
    from models import Taxpayer
    users = Taxpayer.get_all()
    te = sum(u.expected_tax for u in users)
    tpaid = sum(u.tax_paid for u in users)
    print(f"\n{GREEN}{BOLD}SYSTEM STATISTICS{ENDC}")
    print(tabulate([
        ["Total taxpayers", len(users)],
        ["Compliant", sum(1 for u in users if u.compliance_status == "COMPLIANT")],
        ["Underpaid", sum(1 for u in users if u.compliance_status == "UNDERPAID")],
        ["Flagged", sum(1 for u in users if u.flagged)],
        ["High risk (>=70)", sum(1 for u in users if u.risk_score >= 70)],
        ["Expected tax", fmt(te)],
        ["Collected", fmt(tpaid)],
        ["Outstanding", fmt(sum(u.due_amount for u in users))],
        ["Collection rate", f"{(tpaid / te * 100) if te else 100:.1f}%"],
    ], tablefmt="grid") + "\n")


# --- audit + model commands --------------------------------------------------

def cmd_audit(args):
    import audit
    if args.audit_cmd == "verify":
        res = audit.verify_chain()
        if res["ok"]:
            print(f"{GREEN}Ledger intact: {res['length']} events, head {res['head_hash'][:16]}...{ENDC}\n")
        else:
            print(f"{RED}TAMPERING DETECTED at log_id {res['broken_at']}: {res['reason']}{ENDC}\n")
    else:  # trail
        for row in audit.get_trail(args.limit):
            print(f"  #{row['log_id']:<4} {row['timestamp']}  {row['action_type']:<22} {row.get('target_user_id') or '-'}")
        print()


def cmd_model_retrain(args):
    from models import Taxpayer
    from tax_agent import agent
    rows = [t._row for t in Taxpayer.get_all()]
    agent.retrain(rows)
    print(f"{GREEN}Baseline model refit on {len(rows)} live rows + synthetic distribution.{ENDC}\n")


def cmd_admin(args):
    from admin_auth import hash_password, verify_password
    if args.admin_cmd == "login-hash":
        print(hash_password(args.password) + "\n")
    elif args.admin_cmd == "check":
        print(f"{GREEN}match={verify_password(args.password, args.hash)}{ENDC}\n")


# --- parser ------------------------------------------------------------------

def main():
    print_header()
    p = argparse.ArgumentParser(description="RobinHood AI - Tax Administration CLI")
    sub = p.add_subparsers(dest="command")

    c = sub.add_parser("calculate", aliases=["calc"], help="New-regime tax for an income")
    c.add_argument("income", type=float); c.set_defaults(func=cmd_calculate)

    cmp = sub.add_parser("compare", help="Compare multiple incomes")
    cmp.add_argument("incomes", type=float, nargs="+"); cmp.set_defaults(func=cmd_compare)

    sl = sub.add_parser("slabs", help="Show slab tables"); sl.set_defaults(func=cmd_slabs)

    opt = sub.add_parser("optimize", help="Dual-regime optimisation")
    opt.add_argument("income", type=float)
    opt.add_argument("--80c", dest="c80c", type=float, default=0)
    opt.add_argument("--80d", dest="c80d", type=float, default=0)
    opt.add_argument("--hra", type=float, default=0)
    opt.add_argument("--home-loan", dest="home_loan", type=float, default=0)
    opt.add_argument("--senior", action="store_true")
    opt.set_defaults(func=cmd_optimize)

    us = sub.add_parser("users", aliases=["list"], help="List taxpayers"); us.set_defaults(func=cmd_users)
    st = sub.add_parser("stats", help="System statistics"); st.set_defaults(func=cmd_stats)
    rk = sub.add_parser("risk", help="ML anomaly scores"); rk.set_defaults(func=cmd_risk)

    ad = sub.add_parser("add", help="Add taxpayer")
    ad.add_argument("user_id"); ad.add_argument("income", type=float)
    ad.add_argument("--paid", type=float); ad.add_argument("--name"); ad.add_argument("--pan")
    ad.set_defaults(func=cmd_add)

    pay = sub.add_parser("pay", help="Record payment")
    pay.add_argument("user_id"); pay.add_argument("amount", type=float); pay.set_defaults(func=cmd_pay)

    fl = sub.add_parser("flag", help="Toggle flag")
    fl.add_argument("user_id"); fl.set_defaults(func=cmd_flag)

    no = sub.add_parser("notice", help="Send notice")
    no.add_argument("user_id")
    no.add_argument("--type", choices=["reminder", "warning", "final", "penalty"], default="reminder")
    no.set_defaults(func=cmd_notice)

    rm = sub.add_parser("remind-all", help="Persist reminders for all underpayers"); rm.set_defaults(func=cmd_remind_all)

    au = sub.add_parser("audit", help="Ledger operations")
    au.add_argument("audit_cmd", choices=["verify", "trail"])
    au.add_argument("--limit", type=int, default=30); au.set_defaults(func=cmd_audit)

    mo = sub.add_parser("model", help="Model ops")
    mo.add_argument("model_cmd", choices=["retrain"])
    mo.set_defaults(func=lambda a: cmd_model_retrain(a))

    am = sub.add_parser("admin", help="Admin secret utilities")
    am.add_argument("admin_cmd", choices=["login-hash", "check"])
    am.add_argument("--password", default="")
    am.add_argument("--hash", default="")
    am.set_defaults(func=cmd_admin)

    args = p.parse_args()
    if not args.command:
        p.print_help()
        print(f"\n{CYAN}Examples:{ENDC} python robinhood_cli.py optimize 1500000 --80c 150000 --80d 50000")
        print("  python robinhood_cli.py risk\n  python robinhood_cli.py audit verify")
        print("  python robinhood_cli.py admin login-hash --password 'S3cret'\n")
    else:
        args.func(args)


if __name__ == "__main__":
    main()
