from db import get_db_connection

def calculate_tax(income):
    """
    Calculates the tax based on the provided income using a progressive tax system.
    """
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

def get_compliance_status(tax_paid, expected_tax):
    """
    Determines the tax compliance status.
    """
    if tax_paid >= expected_tax:
        return "Compliant"
    elif tax_paid < expected_tax and tax_paid > 0:
        return "Underpaid"
    else:
        return "Overpaid"

def process_payment(user_id, amount):
    """
    Processes a tax payment for a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tax_paid = tax_paid + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Tax payment of {amount} processed for user {user_id}")

def send_warning(user):
    """
    Sends a warning to a user with tax dues.
    """
    print(f"Warning: Tax payment due for user {user.user_id}")

def handle_tax_dues():
    """
    Handles tax dues for all users.
    """
    from models import User  # Import here to avoid circular dependency
    users = User.get_all()
    for user in users:
        expected_tax = calculate_tax(user.declared_income)
        if user.tax_paid < expected_tax:
            send_warning(user)

def send_reminder(user):
    """
    Sends a tax reminder to a user.
    """
    print("----------------------------------------------------")
    print(f"To: {user.user_id}@example.com")
    print("Subject: Reminder: Your Tax Payment is Due")
    print("----------------------------------------------------")
    print(f"Dear {user.user_id},")
    print("\nThis is a reminder that your tax payment is due.")
    print(f"Our records show that you have an outstanding balance of {user.expected_tax - user.tax_paid}.")
    print("\nPlease make the payment at your earliest convenience to avoid penalties.")
    print("\nThank you,")
    print("CivTax System")
    print("----------------------------------------------------")