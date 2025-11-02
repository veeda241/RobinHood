from models import User

def calculate_tax(income):
    if income <= 50000:
        return income * 0.1
    elif income <= 100000:
        return 5000 + (income - 50000) * 0.2
    else:
        return 15000 + (income - 100000) * 0.3

def send_warning(user):
    print(f"Warning: Tax payment due for user {user.user_id}")

def process_payment(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tax_paid = tax_paid + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Tax payment of {amount} processed for user {user_id}")

def handle_tax_dues():
    users = User.get_all()
    for user in users:
        tax_due = calculate_tax(user.declared_income) - user.tax_paid
        if tax_due > 0:
            send_warning(user)
