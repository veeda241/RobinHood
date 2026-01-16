import os
from flask import Flask, request, jsonify, render_template, Blueprint, send_from_directory
from flask_cors import CORS
from models import User
from tax_agent import calculate_tax, send_reminder, send_tax_notice, process_payment, get_detailed_breakdown

app = Flask(__name__, static_folder='frontend/dist', static_url_path='', template_folder='templates')
CORS(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Check if the build folder exists
    if os.path.exists(app.static_folder):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    else:
        # Fallback to legacy UI if build is missing
        return render_template('index.html')

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.get_all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.get_json()
    user = User(
        user_id=data['user_id'],
        declared_income=data['declared_income'],
        tax_paid=data.get('tax_paid', 0)
    )
    user.save()
    return jsonify({'message': 'User added successfully!', 'user': user.to_dict()})

@app.route('/api/users/flag/<user_id>', methods=['PUT'])
def flag_user(user_id):
    User.toggle_flag(user_id)
    return jsonify({'message': f'User {user_id} flag toggled!'})

@app.route('/api/tax/calculate', methods=['POST'])
def calculate_tax_route():
    data = request.get_json()
    income = data['income']
    tax = calculate_tax(income)
    breakdown = get_detailed_breakdown(income)
    return jsonify({'tax': tax, 'breakdown': breakdown})

@app.route('/api/reminders/send/<user_id>', methods=['POST'])
def send_reminder_route(user_id):
    users = User.get_all()
    user = next((u for u in users if u.user_id == user_id), None)
    if user:
        send_reminder(user)
        return jsonify({'message': f'Reminder sent to {user_id}!'})
    return jsonify({'message': 'User not found!'}), 404

@app.route('/api/notices/send/<user_id>', methods=['POST'])
def send_notice_route(user_id):
    data = request.get_json()
    notice_type = data.get('type', 'reminder')
    users = User.get_all()
    user = next((u for u in users if u.user_id == user_id), None)
    if user:
        send_tax_notice(user, notice_type)
        return jsonify({'message': f'Notice sent to {user_id}!', 'type': notice_type})
    return jsonify({'message': 'User not found!'}), 404

@app.route('/api/payments/process', methods=['POST'])
def process_payment_route():
    data = request.get_json()
    user_id = data['user_id']
    amount = data['amount']
    process_payment(user_id, amount)
    return jsonify({'message': f'Payment of {amount} processed for {user_id}!'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    users = User.get_all()
    return jsonify({
        'total': len(users),
        'compliant': sum(1 for u in users if u.compliance_status == 'Compliant'),
        'underpaid': sum(1 for u in users if u.compliance_status == 'Underpaid'),
        'flagged': sum(1 for u in users if u.flagged),
        'total_expected': sum(u.expected_tax for u in users),
        'total_paid': sum(u.tax_paid for u in users),
        'total_due': sum(max(0, u.expected_tax - u.tax_paid) for u in users)
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)