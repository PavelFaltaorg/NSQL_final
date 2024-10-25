# client.py
import requests

BASE_URL = 'https://localhost:8002'

def register(username, password):
    url = f'{BASE_URL}/register'
    payload = {'username': username, 'password': password}
    response = requests.post(url, json=payload, verify=False)
    return response.json()

def login(username, password):
    url = f'{BASE_URL}/login'
    payload = {'username': username, 'password': password}
    response = requests.post(url, json=payload, verify=False)
    return response.json()

def verify(session_id):
    url = f'{BASE_URL}/verify'
    payload = {'session_id': session_id}
    response = requests.post(url, json=payload, verify=False)
    return response.json()

if __name__ == '__main__':
    # Example usage
    username = 'testuser'
    password = 'testpassword'

    # Register a new user
    print('Registering user...')
    register_response = register(username, password)
    print(register_response)

    # Log in with the new user
    print('Logging in...')
    login_response = login(username, password)
    print(login_response)

    # Verify the session
    if 'session_id' in login_response:
        session_id = login_response['session_id']
        print('Verifying session...')
        verify_response = verify(session_id)
        print(verify_response)
    else:
        print('Login failed, cannot verify session.')