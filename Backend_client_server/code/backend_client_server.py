from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

AUTH_SERVER_URL = "http://auth-server:8002"


@app.route('/login', methods=['POST'])
def login():
    # Get credentials from the client frontend
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Username and password are required'}), 400

    # Forward the credentials to the auth server
    try:
        auth_response = requests.post(f"{AUTH_SERVER_URL}/login", json=data)
        # Return the auth server's response to the frontend
        return jsonify(auth_response.json()), auth_response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'message': 'Authentication server is unreachable', 'error': str(e)}), 500

@app.route('/verify', methods=['POST'])
def verify():
    # Get the session ID from the frontend request
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'message': 'Session ID is missing'}), 401

    # Forward the session ID to the auth server for verification
    try:
        auth_response = requests.post(f"{AUTH_SERVER_URL}/verify", json={'session_id': session_id})
        # Relay the auth server's response back to the frontend
        return jsonify(auth_response.json()), auth_response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'message': 'Authentication server is unreachable', 'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=8001)
