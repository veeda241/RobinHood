from flask import Flask, request, jsonify, render_template, Blueprint
from models import User
from tax_agent import calculate_tax, send_reminder

# Create a blueprint for static files
static_bp = Blueprint('static', __name__, static_url_path='/static', static_folder='static')

app = Flask(__name__, template_folder='templates')

# Register the static blueprint
app.register_blueprint(static_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.get_all()
    return jsonify([user.__dict__ for user in users])

@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.get_json()
    user = User(
        user_id=data['user_id'],
        declared_income=data['declared_income']
    )
    user.save()
    return jsonify({'message': 'User added successfully!'})

@app.route('/api/users/flag/<user_id>', methods=['PUT'])
def flag_user(user_id):
    User.flag_user(user_id)
    return jsonify({'message': f'User {user_id} flagged as suspicious!'})

@app.route('/api/tax/calculate', methods=['POST'])
def calculate_tax_route():
    data = request.get_json()
    tax = calculate_tax(data['income'])
    return jsonify({'tax': tax})

@app.route('/api/reminders/send/<user_id>', methods=['POST'])
def send_reminder_route(user_id):
    users = User.get_all()
    user = next((u for u in users if u.user_id == user_id), None)
    if user:
        send_reminder(user)
        return jsonify({'message': f'Reminder sent to {user_id}!'})
    return jsonify({'message': 'User not found!'}), 404

if __name__ == '__main__':
    app.run(port=5000)