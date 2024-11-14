# client.py
import requests

BASE_URL = 'http://0.0.0.0:8002'

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



def verify_session(session_id):
    url = 'http://localhost:8002/verify'
    data = {'session_id': session_id}
    response = requests.post(url, json=data)
    return response.json()

if __name__ == '__main__':
    print(register('test1', 'test'))
    print(login('test1', 'test'))