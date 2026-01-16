"""
RobinHood AI - Tax Agent Module
Handles tax calculations, notices, and compliance management
"""

from db import get_db_connection
from datetime import datetime

# Tax Slabs for New Regime (FY 2024-25)
TAX_SLABS = [
    (300000, 0, 0),           # Up to 3L - NIL
    (600000, 300000, 0.05),   # 3L to 6L - 5%
    (900000, 600000, 0.10),   # 6L to 9L - 10%
    (1200000, 900000, 0.15),  # 9L to 12L - 15%
    (1500000, 1200000, 0.20), # 12L to 15L - 20%
    (float('inf'), 1500000, 0.30) # Above 15L - 30%
]

def calculate_tax(income):
    """Calculate tax based on new regime slabs"""
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

def get_detailed_breakdown(income):
    """Get detailed slab-wise breakdown"""
    breakdown = []
    remaining = income
    
    slabs = [
        {'range': 'Up to ₹3,00,000', 'rate': '0%', 'max': 300000, 'prev': 0},
        {'range': '₹3,00,001 - ₹6,00,000', 'rate': '5%', 'max': 600000, 'prev': 300000},
        {'range': '₹6,00,001 - ₹9,00,000', 'rate': '10%', 'max': 900000, 'prev': 600000},
        {'range': '₹9,00,001 - ₹12,00,000', 'rate': '15%', 'max': 1200000, 'prev': 900000},
        {'range': '₹12,00,001 - ₹15,00,000', 'rate': '20%', 'max': 1500000, 'prev': 1200000},
        {'range': 'Above ₹15,00,000', 'rate': '30%', 'max': float('inf'), 'prev': 1500000},
    ]
    
    rates = [0, 0.05, 0.10, 0.15, 0.20, 0.30]
    
    for i, slab in enumerate(slabs):
        if income > slab['prev']:
            taxable = min(income, slab['max']) - slab['prev']
            tax = taxable * rates[i]
            if tax > 0 or i == 0:
                breakdown.append({
                    'slab': slab['range'],
                    'rate': slab['rate'],
                    'taxable_amount': taxable,
                    'tax': tax
                })
    
    return breakdown

def get_compliance_status(tax_paid, expected_tax):
    """Determine compliance status"""
    if expected_tax == 0:
        return "Compliant"
    if tax_paid >= expected_tax:
        return "Compliant"
    elif tax_paid > 0:
        return "Underpaid"
    else:
        return "Underpaid"

def process_payment(user_id, amount):
    """Process a tax payment"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tax_paid = tax_paid + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✓ Payment of ₹{amount:,.0f} processed for {user_id}")
    return True

def send_reminder(user):
    """Send tax payment reminder"""
    due = user.expected_tax - user.tax_paid
    print("\n" + "="*60)
    print("📧 TAX PAYMENT REMINDER - ROBINHOOD AI")
    print("="*60)
    print(f"To: {user.user_id}@email.com")
    print(f"Subject: Reminder: Tax Payment Due - ₹{due:,.0f}")
    print("-"*60)
    print(f"Dear {user.user_id},\n")
    print("This is a reminder that your tax payment is pending.")
    print(f"\n📊 Tax Summary:")
    print(f"   Declared Income: ₹{user.declared_income:,.0f}")
    print(f"   Expected Tax:    ₹{user.expected_tax:,.0f}")
    print(f"   Tax Paid:        ₹{user.tax_paid:,.0f}")
    print(f"   Outstanding:     ₹{due:,.0f}")
    print("\nPlease make the payment at your earliest convenience.")
    print("\nThank you,")
    print("RobinHood AI Tax System")
    print("="*60 + "\n")

def send_tax_notice(user, notice_type='reminder'):
    """Send official tax notice"""
    due = user.expected_tax - user.tax_paid
    
    notice_templates = {
        'reminder': {
            'subject': 'Payment Reminder',
            'message': 'This is a friendly reminder about your pending tax payment.',
            'urgency': 'LOW'
        },
        'warning': {
            'subject': 'First Warning - Tax Due',
            'message': 'You have not paid your tax dues. Please pay immediately to avoid penalties.',
            'urgency': 'MEDIUM'
        },
        'final': {
            'subject': 'FINAL NOTICE - Immediate Action Required',
            'message': 'This is your final notice. Failure to pay will result in legal action.',
            'urgency': 'HIGH'
        },
        'penalty': {
            'subject': 'PENALTY NOTICE - Additional Charges Applied',
            'message': 'Due to non-payment, a penalty of 10% has been added to your dues.',
            'urgency': 'CRITICAL'
        }
    }
    
    notice = notice_templates.get(notice_type, notice_templates['reminder'])
    
    print("\n" + "🔴"*30)
    print(f"\n📜 OFFICIAL TAX NOTICE - {notice['urgency']} URGENCY")
    print("="*60)
    print(f"NOTICE TYPE: {notice_type.upper()}")
    print(f"DATE: {datetime.now().strftime('%d-%m-%Y')}")
    print(f"REFERENCE: TN/{user.user_id}/{datetime.now().strftime('%Y%m%d')}")
    print("-"*60)
    print(f"TO: {user.user_id}")
    print(f"SUBJECT: {notice['subject']}")
    print("-"*60)
    print(f"\n{notice['message']}\n")
    print(f"TAX DETAILS:")
    print(f"   Income:          ₹{user.declared_income:,.0f}")
    print(f"   Tax Liability:   ₹{user.expected_tax:,.0f}")
    print(f"   Amount Paid:     ₹{user.tax_paid:,.0f}")
    print(f"   Amount Due:      ₹{due:,.0f}")
    
    if notice_type == 'penalty':
        penalty = due * 0.10
        print(f"   Penalty (10%):   ₹{penalty:,.0f}")
        print(f"   TOTAL PAYABLE:   ₹{due + penalty:,.0f}")
    
    print("\n" + "="*60)
    print("INCOME TAX DEPARTMENT - GOVERNMENT OF INDIA")
    print("🔴"*30 + "\n")

def handle_tax_dues():
    """Check and handle all tax dues"""
    from models import User
    users = User.get_all()
    underpaid = [u for u in users if u.compliance_status == 'Underpaid']
    
    print(f"\n📊 Tax Compliance Report")
    print(f"Total Users: {len(users)}")
    print(f"Underpaid: {len(underpaid)}")
    
    for user in underpaid:
        send_reminder(user)
    
    return underpaid