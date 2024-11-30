from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient

app = Flask(__name__)

AUTH_SERVER_URL = "http://auth-server:8002"

client = MongoClient('mongodb://mongo:27017/')
db = client.game
collection = db.game_state

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


@app.route('/changeplayercolor', methods=['POST'])
def change_player_color():
    try:
        # Parse JSON data from the request
        data = request.json

        # Extract RGB values
        red = data.get('red')
        green = data.get('green')
        blue = data.get('blue')

        session_id = data.get('session_id')

        # Combine RGB into a color dictionary for database storage
        new_color = {'r': red, 'g': green, 'b': blue}

        # Simulated authentication (replace with actual implementation)
        auth_response = requests.post(f"{AUTH_SERVER_URL}/verify", json={'session_id': session_id})
        if auth_response.status_code != 200:
            return jsonify({"error": "Authentication failed"}), 401

        player_id = auth_response.json().get('player_id')

        # Update the player's color in the database
        collection.update_one({'player_id': player_id}, {'$set': {'color': new_color}})

        return jsonify({'message': 'Player color updated successfully'}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/changeplayername', methods=['POST'])
def change_player_name():
    try:
        # Parse JSON data from the request
        data = request.json

        # Extract new name
        new_name = data.get('name')

        session_id = data.get('session_id')

        # Simulated authentication (replace with actual implementation)
        auth_response = requests.post(f"{AUTH_SERVER_URL}/verify", json={'session_id': session_id})
        if auth_response.status_code != 200:
            return jsonify({"error": "Authentication failed"}), 401

        player_id = auth_response.json().get('player_id')

        # Update the player's name in the database
        collection.update_one({'player_id': player_id}, {'$set': {'name': new_name}})

        return jsonify({'message': 'Player name updated successfully'}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=8001)
