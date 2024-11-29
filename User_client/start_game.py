import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Game_server.code.game_arcade_client import start_game

session_id = sys.argv[1]
print("test")
start_game(session_id)