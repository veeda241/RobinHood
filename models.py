from db import get_db_connection
from tax_agent import calculate_tax, get_compliance_status

class User:
    def __init__(self, user_id, declared_income, tax_paid=0, flagged=False):
        self.user_id = user_id
        self.declared_income = declared_income
        self.tax_paid = tax_paid
        self.flagged = flagged
        self.expected_tax = calculate_tax(self.declared_income)
        self.compliance_status = get_compliance_status(self.tax_paid, self.expected_tax)

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users_data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        users = []
        for user_data in users_data:
            user = User(
                user_id=user_data['user_id'],
                declared_income=user_data['declared_income'],
                tax_paid=user_data['tax_paid'],
                flagged=user_data['flagged']
            )
            users.append(user)
        return users

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
    def flag_user(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET flagged = TRUE WHERE user_id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()