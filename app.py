from flask import Flask, request, jsonify
from flask_cors import CORS
import schedule
import time
from models import User
from tax_agent import calculate_tax, process_payment, handle_tax_dues
from db import get_db_connection

app = Flask(__name__)
CORS(app)

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    default_users = [
        User("user1", 60000, "Groceries, Rent, Salary", "Salary"),
        User("user2", 120000, "Stock investments, Dividends, Luxury goods", "Investments"),
        User("user3", 40000, "Freelance work, Online sales", "Freelance"),
    ]
    for user in default_users:
        user.save()
    conn.close()

def run_demonstration():
    setup_database()
    users = User.get_all()
    for user in users:
        tax = calculate_tax(user.declared_income)
        print(f"Tax for {user.user_id}: {tax}")
        process_payment(user.user_id, tax / 2)
    User.flag_user("user2")

@app.route('/')
def index():
    return 'Welcome to Robinhood Backend 🚀'

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.get_all()
    return jsonify([user.__dict__ for user in users])

@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.get_json()
    user = User(
        user_id=data['user_id'],
        declared_income=data['declared_income'],
        observed_transactions=data['observed_transactions'],
        income_source=data['income_source']
    )
    user.save()
    return 'User added successfully!'

@app.route('/api/users/flag/<user_id>', methods=['PUT'])
def flag_user(user_id):
    User.flag_user(user_id)
    return f'User {user_id} flagged as suspicious!'

@app.route('/api/tax/calculate', methods=['POST'])
def calculate_tax_route():
    data = request.get_json()
    tax = calculate_tax(data['income'])
    return jsonify({'tax': tax})

@app.route('/api/tax/pay', methods=['POST'])
def pay_tax_route():
    data = request.get_json()
    process_payment(data['userId'], data['amount'])
    return 'Payment processed successfully!'

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    run_demonstration()
    schedule.every().day.at("00:00").do(handle_tax_dues)
    import threading
    threading.Thread(target=run_schedule).start()
    app.run(port=5000)
