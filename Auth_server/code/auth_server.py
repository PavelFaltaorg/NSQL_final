from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')

# In-memory database for demonstration purposes
users_db = {}
sessions_db = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if username in users_db:
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    users_db[username] = {
        'id': str(uuid.uuid4()),
        'password': hashed_password
    }

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = users_db.get(username)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    session_id = str(uuid.uuid4())
    sessions_db[session_id] = {
        'user_id': user['id'],
        'expires_at': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }

    return jsonify({'session_id': session_id})

@app.route('/verify', methods=['POST'])
def verify():
    return jsonify({'message': 'Session verified'}), 200 # For testing purposes
    data = request.get_json()
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'message': 'Session ID is missing'}), 401

    session = sessions_db.get(session_id)
    if not session or session['expires_at'] < datetime.datetime.now(datetime.timezone.utc):
        return jsonify({'message': 'Session is invalid or expired'}), 401

    return jsonify({'message': 'Session verified'}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True, port=8002, ssl_context='adhoc')