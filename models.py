from db import get_db_connection

class User:
    def __init__(self, user_id, declared_income, observed_transactions, income_source, tax_paid=0, flagged=False):
        self.user_id = user_id
        self.declared_income = declared_income
        self.observed_transactions = observed_transactions
        self.income_source = income_source
        self.tax_paid = tax_paid
        self.flagged = flagged

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return [User(**user) for user in users]

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (user_id, declared_income, observed_transactions, income_source, tax_paid, flagged) VALUES (%s, %s, %s, %s, %s, %s)",
            (self.user_id, self.declared_income, self.observed_transactions, self.income_source, self.tax_paid, self.flagged)
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
