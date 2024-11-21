from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os
import redis
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')

# In-memory database for demonstration purposes
sessions_db = {}

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = os.getenv('REDIS_PORT', 6379)
redis_db = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if redis_db.exists(username):
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    user_data = {
        'id': str(uuid.uuid4()),
        'password': hashed_password
    }
    redis_db.set(username, json.dumps(user_data))

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user_data = redis_db.get(username)
    if not user_data:
        return jsonify({'message': 'Invalid credentials'}), 401

    user = json.loads(user_data)
    if not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    session_id = str(uuid.uuid4())
    sessions_db[session_id] = {
        'user_id': user['id']
    }

    return jsonify({'session_id': session_id})

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'message': 'Session ID is missing'}), 401

    session = sessions_db.get(session_id)
    if not session:
        return jsonify({'message': 'Session is invalid'}), 401

    return jsonify({'message': 'Session verified', 'player_id': session['user_id']}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=8002)
