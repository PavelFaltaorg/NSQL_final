import redis

# Connect to Redis server with full access
r = redis.Redis(host='localhost', port=1111, db=0, username='db_user', password='db_pwd')

def set_user_session(user_id, session_data):
    r.set(user_id, session_data)

def get_user_session(user_id):
    return r.get(user_id)

# Example usage
if __name__ == "__main__":
    #set_user_session('user123', 'session_data_example') #set command will fail for db_user, as it does not have write access
    session = get_user_session('user123')
    print(session)