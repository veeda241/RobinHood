#!/usr/bin/env python3
"""
RobinHood AI - Administration CLI
A powerful command-line interface for tax administration and calculations
"""

import argparse
import sys
import os

# Fix Windows encoding issues
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from tabulate import tabulate

# Colors for terminal output (using colorama for Windows compatibility)
try:
    from colorama import init, Fore, Style
    init()
    HEADER = Fore.MAGENTA
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    ENDC = Style.RESET_ALL
    BOLD = Style.BRIGHT
except ImportError:
    HEADER = BLUE = CYAN = GREEN = YELLOW = RED = ENDC = BOLD = ''

def print_header():
    """Print CLI header"""
    print(f"\n{CYAN}{BOLD}")
    print("=" * 60)
    print("       ROBINHOOD AI - TAX ADMIN CLI")
    print("       Smart Tax Compliance Management System")
    print("=" * 60)
    print(f"{ENDC}")

def format_currency(amount):
    """Format number as Indian currency"""
    return f"Rs.{amount:,.0f}"

def calculate_tax(income):
    """Calculate tax based on new regime"""
    if income <= 300000:
        return 0
    elif income <= 600000:
        return (income - 300000) * 0.05
    elif income <= 900000:
        return 15000 + (income - 600000) * 0.10
    elif income <= 1200000:
        return 45000 + (income - 900000) * 0.15
    elif income <= 1500000:
        return 90000 + (income - 1200000) * 0.20
    else:
        return 150000 + (income - 1500000) * 0.30

def get_breakdown(income):
    """Get slab-wise breakdown"""
    slabs = []
    
    if income <= 300000:
        slabs.append(("Up to 3L", "NIL", income, 0))
        return slabs
    
    slabs.append(("Up to 3L", "0%", 300000, 0))
    
    if income > 300000:
        taxable = min(income, 600000) - 300000
        slabs.append(("3L - 6L", "5%", taxable, taxable * 0.05))
    
    if income > 600000:
        taxable = min(income, 900000) - 600000
        slabs.append(("6L - 9L", "10%", taxable, taxable * 0.10))
    
    if income > 900000:
        taxable = min(income, 1200000) - 900000
        slabs.append(("9L - 12L", "15%", taxable, taxable * 0.15))
    
    if income > 1200000:
        taxable = min(income, 1500000) - 1200000
        slabs.append(("12L - 15L", "20%", taxable, taxable * 0.20))
    
    if income > 1500000:
        taxable = income - 1500000
        slabs.append(("Above 15L", "30%", taxable, taxable * 0.30))
    
    return slabs

def cmd_calculate(args):
    """Calculate tax for given income"""
    income = args.income
    tax = calculate_tax(income)
    breakdown = get_breakdown(income)
    
    print(f"\n{GREEN}{BOLD}TAX CALCULATION REPORT{ENDC}")
    print("=" * 60)
    print(f"Income: {BOLD}{format_currency(income)}{ENDC}")
    print(f"Assessment Year: 2025-26 (FY 2024-25)")
    print("-" * 60)
    
    print(f"\n{CYAN}Slab-wise Breakdown:{ENDC}")
    headers = ["Slab", "Rate", "Taxable Amount", "Tax"]
    table_data = [(s[0], s[1], format_currency(s[2]), format_currency(s[3])) for s in breakdown]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    print("-" * 60)
    print(f"{BOLD}TOTAL TAX PAYABLE: {GREEN}{format_currency(tax)}{ENDC}")
    
    if income > 0:
        effective_rate = (tax / income) * 100
        print(f"Effective Tax Rate: {effective_rate:.2f}%")
    
    print(f"\n{CYAN}Monthly Summary:{ENDC}")
    monthly_income = income / 12
    monthly_tax = tax / 12
    print(f"  Monthly Income: {format_currency(monthly_income)}")
    print(f"  Monthly Tax:    {format_currency(monthly_tax)}")
    print(f"  Take Home:      {format_currency(monthly_income - monthly_tax)}")
    print("=" * 60 + "\n")

def cmd_compare(args):
    """Compare tax for different incomes"""
    incomes = args.incomes
    
    print(f"\n{GREEN}{BOLD}TAX COMPARISON REPORT{ENDC}")
    print("=" * 60)
    
    data = []
    for income in incomes:
        tax = calculate_tax(income)
        rate = (tax / income * 100) if income > 0 else 0
        take_home = income - tax
        data.append([
            format_currency(income),
            format_currency(tax),
            f"{rate:.2f}%",
            format_currency(take_home)
        ])
    
    headers = ["Income", "Tax", "Effective Rate", "Take Home"]
    print(tabulate(data, headers=headers, tablefmt="grid"))
    print()

def cmd_slabs(args):
    """Display current tax slabs"""
    print(f"\n{GREEN}{BOLD}TAX SLABS - NEW REGIME (FY 2024-25){ENDC}")
    print("=" * 60)
    
    slabs = [
        ["Up to Rs.3,00,000", "NIL", "Rs.0"],
        ["Rs.3,00,001 - Rs.6,00,000", "5%", "Rs.15,000 max"],
        ["Rs.6,00,001 - Rs.9,00,000", "10%", "Rs.30,000 max"],
        ["Rs.9,00,001 - Rs.12,00,000", "15%", "Rs.45,000 max"],
        ["Rs.12,00,001 - Rs.15,00,000", "20%", "Rs.60,000 max"],
        ["Above Rs.15,00,000", "30%", "No limit"],
    ]
    
    headers = ["Income Range", "Tax Rate", "Max Tax in Slab"]
    print(tabulate(slabs, headers=headers, tablefmt="grid"))
    
    print(f"\n{YELLOW}Note: Standard deduction of Rs.50,000 available for salaried individuals{ENDC}")
    print()

def cmd_users(args):
    """List all users with their tax status"""
    try:
        from models import User
        users = User.get_all()
        
        print(f"\n{GREEN}{BOLD}TAXPAYER REGISTRY{ENDC}")
        print("=" * 80)
        
        data = []
        for u in users:
            flag = "[FLAGGED]" if u.flagged else ""
            data.append([
                f"{u.user_id} {flag}",
                format_currency(u.declared_income),
                format_currency(u.expected_tax),
                format_currency(u.tax_paid),
                format_currency(u.due_amount),
                u.compliance_status
            ])
        
        headers = ["User ID", "Income", "Expected Tax", "Paid", "Due", "Status"]
        print(tabulate(data, headers=headers, tablefmt="grid"))
        
        total_expected = sum(u.expected_tax for u in users)
        total_paid = sum(u.tax_paid for u in users)
        total_due = sum(u.due_amount for u in users)
        compliant = sum(1 for u in users if u.compliance_status == 'Compliant')
        
        print(f"\n{CYAN}Summary:{ENDC}")
        print(f"  Total Users: {len(users)}")
        print(f"  Compliant: {GREEN}{compliant}{ENDC}")
        print(f"  Non-Compliant: {RED}{len(users) - compliant}{ENDC}")
        print(f"  Total Expected: {format_currency(total_expected)}")
        print(f"  Total Collected: {format_currency(total_paid)}")
        print(f"  Total Outstanding: {RED}{format_currency(total_due)}{ENDC}")
        print()
    except Exception as e:
        print(f"{RED}Error: Could not connect to database. {e}{ENDC}")

def cmd_notice(args):
    """Send tax notice to a user"""
    try:
        from models import User
        from tax_agent import send_tax_notice
        
        user = User.get_by_id(args.user_id)
        if user:
            send_tax_notice(user, args.type)
            print(f"\n{GREEN}Notice sent successfully to {args.user_id}{ENDC}\n")
        else:
            print(f"\n{RED}User {args.user_id} not found{ENDC}\n")
    except Exception as e:
        print(f"{RED}Error: {e}{ENDC}")

def cmd_remind(args):
    """Send reminders to all underpaid users"""
    try:
        from models import User
        from tax_agent import send_reminder
        
        users = User.get_all()
        underpaid = [u for u in users if u.compliance_status == 'Underpaid']
        
        print(f"\n{YELLOW}Sending reminders to {len(underpaid)} underpaid users...{ENDC}\n")
        
        for user in underpaid:
            send_reminder(user)
        
        print(f"\n{GREEN}Sent {len(underpaid)} reminders{ENDC}\n")
    except Exception as e:
        print(f"{RED}Error: {e}{ENDC}")

def cmd_add(args):
    """Add a new taxpayer"""
    try:
        from models import User
        
        user = User(
            user_id=args.user_id,
            declared_income=args.income,
            tax_paid=args.paid or 0
        )
        user.save()
        
        print(f"\n{GREEN}Taxpayer {args.user_id} added successfully!{ENDC}")
        print(f"  Income: {format_currency(args.income)}")
        print(f"  Expected Tax: {format_currency(user.expected_tax)}")
        print(f"  Tax Paid: {format_currency(user.tax_paid)}")
        print(f"  Status: {user.compliance_status}\n")
    except Exception as e:
        print(f"{RED}Error: {e}{ENDC}")

def cmd_pay(args):
    """Process a tax payment"""
    try:
        from models import User
        
        User.update_tax_paid(args.user_id, args.amount)
        print(f"\n{GREEN}Payment of {format_currency(args.amount)} recorded for {args.user_id}{ENDC}\n")
    except Exception as e:
        print(f"{RED}Error: {e}{ENDC}")

def cmd_flag(args):
    """Flag/unflag a user for review"""
    try:
        from models import User
        
        User.toggle_flag(args.user_id)
        print(f"\n{YELLOW}Flag toggled for user {args.user_id}{ENDC}\n")
    except Exception as e:
        print(f"{RED}Error: {e}{ENDC}")

def cmd_stats(args):
    """Show system statistics"""
    try:
        from models import User
        
        users = User.get_all()
        
        print(f"\n{GREEN}{BOLD}SYSTEM STATISTICS{ENDC}")
        print("=" * 60)
        
        total = len(users)
        compliant = sum(1 for u in users if u.compliance_status == 'Compliant')
        underpaid = total - compliant
        flagged = sum(1 for u in users if u.flagged)
        
        total_income = sum(u.declared_income for u in users)
        total_expected = sum(u.expected_tax for u in users)
        total_paid = sum(u.tax_paid for u in users)
        total_due = sum(u.due_amount for u in users)
        
        collection_rate = (total_paid / total_expected * 100) if total_expected > 0 else 100
        
        print(f"\n{CYAN}Taxpayer Overview:{ENDC}")
        print(f"  Total Registered: {total}")
        if total > 0:
            print(f"  Compliant:        {GREEN}{compliant}{ENDC} ({compliant/total*100:.1f}%)")
            print(f"  Non-Compliant:    {RED}{underpaid}{ENDC} ({underpaid/total*100:.1f}%)")
        print(f"  Flagged:          {YELLOW}{flagged}{ENDC}")
        
        print(f"\n{CYAN}Financial Summary:{ENDC}")
        print(f"  Total Declared Income:  {format_currency(total_income)}")
        print(f"  Total Expected Tax:     {format_currency(total_expected)}")
        print(f"  Total Collected:        {GREEN}{format_currency(total_paid)}{ENDC}")
        print(f"  Outstanding Amount:     {RED}{format_currency(total_due)}{ENDC}")
        print(f"  Collection Rate:        {collection_rate:.1f}%")
        
        print("\n" + "=" * 60 + "\n")
    except Exception as e:
        print(f"{RED}Error: {e}{ENDC}")

def main():
    print_header()
    
    parser = argparse.ArgumentParser(
        description='RobinHood AI - Tax Administration CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Calculate command
    calc_parser = subparsers.add_parser('calculate', aliases=['calc'], help='Calculate tax for an income')
    calc_parser.add_argument('income', type=float, help='Annual income amount')
    calc_parser.set_defaults(func=cmd_calculate)
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare tax for multiple incomes')
    compare_parser.add_argument('incomes', type=float, nargs='+', help='Income amounts to compare')
    compare_parser.set_defaults(func=cmd_compare)
    
    # Slabs command
    slabs_parser = subparsers.add_parser('slabs', help='Display current tax slabs')
    slabs_parser.set_defaults(func=cmd_slabs)
    
    # Users command
    users_parser = subparsers.add_parser('users', aliases=['list'], help='List all taxpayers')
    users_parser.set_defaults(func=cmd_users)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show system statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Add user command
    add_parser = subparsers.add_parser('add', help='Add a new taxpayer')
    add_parser.add_argument('user_id', help='User ID')
    add_parser.add_argument('income', type=float, help='Declared income')
    add_parser.add_argument('--paid', type=float, help='Tax already paid')
    add_parser.set_defaults(func=cmd_add)
    
    # Pay command
    pay_parser = subparsers.add_parser('pay', help='Record a tax payment')
    pay_parser.add_argument('user_id', help='User ID')
    pay_parser.add_argument('amount', type=float, help='Payment amount')
    pay_parser.set_defaults(func=cmd_pay)
    
    # Notice command
    notice_parser = subparsers.add_parser('notice', help='Send tax notice to user')
    notice_parser.add_argument('user_id', help='User ID')
    notice_parser.add_argument('--type', choices=['reminder', 'warning', 'final', 'penalty'], 
                               default='reminder', help='Notice type')
    notice_parser.set_defaults(func=cmd_notice)
    
    # Remind command
    remind_parser = subparsers.add_parser('remind', help='Send reminders to all underpaid users')
    remind_parser.set_defaults(func=cmd_remind)
    
    # Flag command
    flag_parser = subparsers.add_parser('flag', help='Toggle flag on a user')
    flag_parser.add_argument('user_id', help='User ID to flag/unflag')
    flag_parser.set_defaults(func=cmd_flag)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        print(f"\n{CYAN}Quick Examples:{ENDC}")
        print("  python robinhood_cli.py calculate 1200000")
        print("  python robinhood_cli.py compare 500000 1000000 1500000")
        print("  python robinhood_cli.py slabs")
        print("  python robinhood_cli.py users")
        print("  python robinhood_cli.py stats")
        print("  python robinhood_cli.py add USER001 800000 --paid 25000")
        print("  python robinhood_cli.py pay USER001 50000")
        print("  python robinhood_cli.py notice USER001 --type warning")
        print()
    else:
        args.func(args)

if __name__ == '__main__':
    main()
