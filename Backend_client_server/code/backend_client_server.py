from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

AUTH_SERVER_URL = "http://127.0.0.1:8002"

@app.route('/login', methods=['POST'])
def login():
    credentials = request.json
    if not credentials or 'username' not in credentials or 'password' not in credentials:
        return jsonify({"error": "Invalid payload"}), 400

    # Forward login request to auth server
    auth_response = requests.post(f"{AUTH_SERVER_URL}/login", json=credentials)
    if auth_response.status_code == 200:
        return jsonify(auth_response.json()), 200
    else:
        return jsonify({"error": "Authentication failed"}), auth_response.status_code

@app.route('/verify', methods=['GET'])
def validate():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Token required"}), 400

    # Validate token with auth server
    validate_response = requests.get(f"{AUTH_SERVER_URL}/verify", headers={"Authorization": token})
    if validate_response.status_code == 200:
        return jsonify(validate_response.json()), 200
    else:
        return jsonify({"error": "Invalid token"}), validate_response.status_code



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=8001)
