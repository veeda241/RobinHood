from db import get_db_connection
from tax_agent import calculate_tax, get_compliance_status

class User:
    def __init__(self, user_id, declared_income, tax_paid=0, flagged=False):
        self.user_id = user_id
        self.declared_income = declared_income
        self.tax_paid = tax_paid
        self.flagged = bool(flagged)
        self.expected_tax = calculate_tax(self.declared_income)
        self.compliance_status = get_compliance_status(self.tax_paid, self.expected_tax)
        self.due_amount = max(0, self.expected_tax - self.tax_paid)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'declared_income': self.declared_income,
            'tax_paid': self.tax_paid,
            'expected_tax': self.expected_tax,
            'compliance_status': self.compliance_status,
            'flagged': self.flagged,
            'due_amount': self.due_amount
        }

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users_data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [User(
            user_id=u['user_id'],
            declared_income=u['declared_income'],
            tax_paid=u['tax_paid'],
            flagged=u['flagged']
        ) for u in users_data]

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data:
            return User(
                user_id=user_data['user_id'],
                declared_income=user_data['declared_income'],
                tax_paid=user_data['tax_paid'],
                flagged=user_data['flagged']
            )
        return None

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (user_id, declared_income, tax_paid, flagged) VALUES (%s, %s, %s, %s)",
            (self.user_id, self.declared_income, self.tax_paid, self.flagged)
        )
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def toggle_flag(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET flagged = NOT flagged WHERE user_id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def update_tax_paid(user_id, amount):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET tax_paid = tax_paid + %s WHERE user_id = %s", (amount, user_id))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def delete(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()