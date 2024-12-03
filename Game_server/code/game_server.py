import threading
import time
import game_pb2
import pymunk
from pymunk import Vec2d
from dataclasses import dataclass
from typing import Tuple, Dict
import zstandard as zstd
from collections import deque
from uuid import uuid4
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import redis
import requests
from pymongo import MongoClient
from coolname import generate
import random

BULLET_COLLISION_TYPE = 1
PLAYER_COLLISION_TYPE = 2
TERRAIN_COLLISION_TYPE = 3
NO_CLIP_COLLISION_TYPE = 999

SEND_INTERVAL = 15

PLAYER_SPEED = 1500
BULLET_SPEED = 1500
SEND_DISTANCE_THRESHOLD = 1000

@dataclass
class Player:
    player_id: str
    body: pymunk.Body
    shape: pymunk.Shape
    direction: Vec2d
    addr: Tuple[str, int]
    last_update: float
    strikes: int
    hp: float
    max_hp: float
    hp_regen_rate: float
    last_hit: str
    name: str
    dead: bool
    color: Tuple
    invincible: bool

@dataclass
class Bullet:
    body: pymunk.Body
    shape: pymunk.Shape
    owner_id: str
    damage: float
    positions: deque

@dataclass
class Terrain:
    position: Vec2d
    size: Vec2d
    color: Tuple
    shape: str
    bounding: bool
    no_clip: bool

class Leaderboard:
    def __init__(self):
        self.scores = {}
        self.lock = threading.Lock()

    def add_points(self, session_id, points=0, reset=False):
        with self.lock:
            if session_id not in self.scores:
                self.scores[session_id] = {"color": (0,0,0), "name": "", "points": 0}
            if reset:
                self.scores[session_id]["points"] = 0
            else:
                self.scores[session_id]["points"] += points
    
    def update(self, players):
        with self.lock:
            for session_id, player_data in self.scores.items():
                if session_id in self.scores:
                    player_data["color"] = players[session_id].color
                    player_data["name"] = players[session_id].name

    def create_new(self, session_id, player_name, player_color):

        self.scores[session_id] = {
            "color": player_color,
            "name": player_name,
            "points": 0
        }

    def remove_player(self, session_id):
        with self.lock:
            if session_id in self.scores:
                self.scores.pop(session_id)

    def serialize(self, current_session_id):
        n = 5
        with self.lock:
            sorted_scores = sorted(self.scores.items(), key=lambda item: item[1]["points"], reverse=True)
            top_n = sorted_scores[:n]
    
            # Check if the current player is in the top N
            current_player_in_top_n = any(session_id == current_session_id for session_id, _ in top_n)
    
            if not current_player_in_top_n and current_session_id in self.scores:
                current_player_score = self.scores[current_session_id]
                top_n.append((current_session_id, current_player_score))
    
            return [{"color": player_data["color"], "name": player_data["name"], "points": player_data["points"]} for session_id, player_data in top_n]

class Game:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.bullets: Dict[str, Bullet] = {}
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.lock = threading.Lock()
        self.max_strikes = 1  # TODO change in future
        self.last_bullet_id = 0
        self.map_size = 1000
        self.id_mask_map = {}
        self.leaderboard = Leaderboard()
        self.message_buffer = deque()

    def add_player(self, player_input, addr: Tuple[str, int], pid): # in the future change to load player data from mongodb edit: already done dumbass
        print(f"Adding player with session_id: {player_input.session_id} and player_id: {pid}")
        player_data = collection.find_one({"player_id": pid})
        session_id = player_input.session_id
        if player_data:
            print(f"Found existing player data for player_id: {pid}: {player_data}")
            body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 20))
            body.position = player_data["position"]
            shape = pymunk.Circle(body, 20)
            shape.collision_type = PLAYER_COLLISION_TYPE
            self.space.add(body, shape)
            self.id_mask_map[session_id] = str(uuid4())

            self.players[session_id] = Player(
                player_id=pid,
                body=body,
                shape=shape,
                direction=Vec2d(0, 0),
                addr=addr,
                last_update=time.time(),
                strikes=0,
                hp=player_data["hp"],
                max_hp=player_data["max_hp"],
                hp_regen_rate=player_data["hp_regen_rate"],
                last_hit=player_data["last_hit"],
                name=player_data["name"],
                dead=player_data["dead"],
                color=game_pb2.Color(r=player_data["color"][0], g=player_data["color"][1], b=player_data["color"][2]),
                invincible=True
            )
            print(self.players)
        else:
            print(f"No existing player data found for player_id: {pid}, creating new player")
            body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 20))
            body.position = 0, 0
            shape = pymunk.Circle(body, 20)
            shape.collision_type = PLAYER_COLLISION_TYPE
            self.space.add(body, shape)
            self.id_mask_map[session_id] = str(uuid4())

            rancolor = (random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))

            self.players[session_id] = Player(
                player_id=pid,
                body=body,
                shape=shape,
                direction=Vec2d(0, 0),
                addr=addr,
                last_update=time.time(),
                strikes=0,
                hp=1000,
                max_hp=1000,
                hp_regen_rate=0.5,
                last_hit=None,
                name=' '.join(x.capitalize() for x in generate(2)),
                dead=False,
                color=game_pb2.Color(r=rancolor[0], g=rancolor[1], b=rancolor[2]),
                invincible=True
            )
            # Save the player data to the database
            collection.update_one(
                {"player_id": pid},
                {"$set": {
                    "position": body.position,
                    "hp": self.players[player_input.session_id].hp,
                    "max_hp": self.players[player_input.session_id].max_hp,
                    "hp_regen_rate": self.players[player_input.session_id].hp_regen_rate,
                    "last_hit": self.players[player_input.session_id].last_hit,
                    "name": self.players[player_input.session_id].name,
                    "dead": self.players[player_input.session_id].dead,
                    "color": (self.players[player_input.session_id].color.r, self.players[player_input.session_id].color.g, self.players[player_input.session_id].color.b)
                }},
                upsert=True
            )
            print(f"New player data saved for player_id: {pid}")
        player_name = self.players[session_id].name
        player_color = self.players[session_id].color
        self.leaderboard.create_new(session_id, player_name, player_color)

        self.message_buffer.append(game_pb2.ServerMessage(type=0, content=f"{player_name} Joined."))
        print(f"Player {player_name} with session_id: {player_input.session_id} joined the game.")

    def respawn_player(self, session_id):
        player = self.players.get(session_id)
        if player:
            player.body.position = 0, 0
            player.body.velocity = 0, 0
            player.hp = player.max_hp
            player.dead = False
            player.last_hit = None
            player.strikes = 0
            player.invincible = True
            self.leaderboard.add_points(session_id, reset=True)

    def remove_player(self, session_id: int):
        player = self.players.pop(session_id, None)
        if player:
            self.space.remove(player.body, player.shape)
            self.leaderboard.remove_player(session_id)
            self.message_buffer.append(game_pb2.ServerMessage(type=0, content=f"{player.name} Disconnected."))
            print(f"Player {session_id} removed from the game.")

    def process_input(self, data: bytes, addr: Tuple[str, int], session_id: str, pid: str):
        player_input = self.deserialize_input(data)
        player_input.session_id = session_id
        if player_input.message:
            player_name = self.players[session_id].name
            player_color = self.players[session_id].color
            self.message_buffer.append(
                game_pb2.ServerMessage(type=1, header=player_name, content=player_input.message, color=player_color))

        with self.lock:
            if session_id not in self.players:
                self.add_player(player_input, addr, pid)
            else:
                player = self.players[session_id]
                player.addr = addr
                player.last_update = time.time()
                player.strikes = 0

            self.update_player_state(player_input)

    def update_player_state(self, player_input):
        player = self.players.get(player_input.session_id)
        if player:
            if not player.dead:
                player.direction = Vec2d(player_input.direction_x, player_input.direction_y).normalized()
                if player_input.shoot:
                    if player.invincible:
                        player.invincible = False
                    self.add_bullet(player_input)
            else:
                if player_input.respawn:
                    self.respawn_player(player_input.session_id)

    def add_bullet(self, player_input):
        player = self.players.get(player_input.session_id)
        if player:
            bullet_body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 5))
            bullet_body.position = player.body.position
            bullet_shape = pymunk.Circle(bullet_body, 5)
            bullet_shape.sensor = True
            bullet_shape.collision_type = BULLET_COLLISION_TYPE

            cursor_position = Vec2d(player_input.target_position_x, player_input.target_position_y)
            distance_to_cursor = (cursor_position - player.body.position).length

            time_step = -(distance_to_cursor / BULLET_SPEED)

            future_position = player.body.position + player.body.velocity * time_step

            direction = cursor_position - future_position

            if direction.length > 0:
                direction = direction.normalized()

            bullet_body.velocity = direction * BULLET_SPEED

            self.space.add(bullet_body, bullet_shape)

            bullet_id = self.last_bullet_id
            self.last_bullet_id += 1

            self.bullets[bullet_id] = Bullet(
                body=bullet_body,
                shape=bullet_shape,
                owner_id=player_input.session_id,
                damage=5,
                positions=deque([bullet_body.position], maxlen=2)
            )

    def remove_bullet(self, bullet_id):
        bullet = self.bullets.pop(bullet_id, None)
        if bullet:
            self.space.remove(bullet.body, bullet.shape)

    def update_physics(self, dt: float):
        with self.lock:
            for player in self.players.values():
                if not player.dead:
                    if player.direction.length > 0:
                        player.body.apply_force_at_local_point(player.direction * PLAYER_SPEED)
                    player.body.velocity *= 0.95

                    if player.hp < player.max_hp:
                        player.hp = min(player.hp + player.hp_regen_rate * dt, player.max_hp)

                    if player.hp <= 0:
                        player.dead = True
                        self.leaderboard.add_points(player.last_hit, player.max_hp)
                        print(f"Player {player.name} died.")
                        self.message_buffer.append(game_pb2.ServerMessage(type=0, content=f"{self.players[player.last_hit].name} Killed {player.name}."))

            for bullet_id, bullet in list(self.bullets.items()):
                bullet.positions.append(bullet.body.position)

                if len(bullet.positions) == 2:
                    start_point, end_point = bullet.positions
                    raycast_info = self.space.segment_query_first(start_point, end_point, 1, pymunk.ShapeFilter())

                    if raycast_info:
                        hit_shape = raycast_info.shape
                        if hit_shape.collision_type == PLAYER_COLLISION_TYPE:

                            session_id = next(pid for pid, p in self.players.items() if p.shape == hit_shape)
                            player = self.players[session_id]

                            if bullet.owner_id != session_id and player.hp > 0:
                                self.deal_dmg(player, bullet.owner_id, bullet.damage)
                                self.remove_bullet(bullet_id)

                        elif hit_shape.collision_type == TERRAIN_COLLISION_TYPE:
                            self.remove_bullet(bullet_id)

            self.space.step(dt)

    def serialize_game_state(self) -> dict:
        self.leaderboard.update(self.players)
        send_message = False
        game_states = {}
        with self.lock:
            if self.message_buffer:
                chat_message = self.message_buffer.popleft()
                send_message = True
            for session_id in self.players.keys():
                game_state = game_pb2.GameState()
                if send_message:
                    game_state.message.CopyFrom(chat_message)
                game_state.map_size = self.map_size
                game_state.timestamp = time.time_ns()
                game_state.server_fps = SEND_INTERVAL

                leaderboard_entries = self.leaderboard.serialize(session_id)  # Top 10 players + current player
                for entry in leaderboard_entries:
                    game_state.leaderboard.add(color=entry["color"], name=entry["name"], points=entry["points"])

                current_player = self.players[session_id]
                if current_player.hp <= 0 and self.players.get(current_player.last_hit):
                    current_position = self.players[current_player.last_hit].body.position
                else:
                    current_position = current_player.body.position

                for other_session_id, player in self.players.items():
                    position = player.body.position
                    velocity = player.body.velocity
                    game_state.players.add(
                        id=session_id if session_id == other_session_id else self.id_mask_map[other_session_id],
                        x=position.x,
                        y=position.y,
                        hp=player.hp,
                        last_hit=self.id_mask_map.get(player.last_hit, None),
                        vx=velocity.x,
                        vy=velocity.y,
                        name=player.name,
                        max_hp=player.max_hp,
                        color=player.color if not player.dead else game_pb2.Color(r=0, g=0, b=0)
                    )

                for bullet_id, bullet in self.bullets.items():
                    position = bullet.body.position
                    if current_position.get_distance(position) <= SEND_DISTANCE_THRESHOLD:
                        velocity = bullet.body.velocity
                        game_state.bullets.add(
                            id=bullet_id,
                            x=position.x,
                            y=position.y,
                            vx=velocity.x,
                            vy=velocity.y
                        )

                cctx = zstd.ZstdCompressor()
                game_states[session_id] = cctx.compress(game_state.SerializeToString())

        return game_states

    def deserialize_input(self, data: bytes) -> game_pb2.PlayerInput:
        proto = game_pb2.PlayerInput()
        proto.ParseFromString(data)
        return proto

    def check_player_timeout(self):
        while True:
            current_time = time.time()
            with self.lock:
                for session_id, player in list(self.players.items()):
                    if current_time - player.last_update > 5:  # 5 seconds timeout
                        player.strikes += 1
                        if player.strikes >= self.max_strikes:
                            self.remove_player(session_id)
            time.sleep(5)  # Check every 5s

    def deal_dmg(self, receiver, dealer_id, damage):
        if not receiver.invincible:
            if hasattr(receiver, "shield"):
                overflow = 0
                if receiver.shield > 0:
                    if receiver.shield < damage:
                        overflow = receiver.shield - damage
                    receiver.shield -= damage
                    receiver.last_hit = dealer_id
                    receiver.hp += overflow
                else:
                    receiver.last_hit = dealer_id
                    receiver.hp = round(receiver.hp - damage, 2)
                if hasattr(receiver, "last_hit_timer"):
                    receiver.last_hit_timer = 0
            else:
                receiver.last_hit = dealer_id
                receiver.hp = round(receiver.hp - damage, 2)
                if hasattr(receiver, "last_hit_timer"):
                    receiver.last_hit_timer = 0
            self.leaderboard.add_points(dealer_id, damage)

    def add_terrain(self, lst):
        for terrain in lst:
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = terrain.position
            if terrain.shape == "r":
                shape = pymunk.Poly.create_box(body, terrain.size)
            elif terrain.shape == "c":
                shape = pymunk.Circle(body, terrain.size[0])
            shape.collision_type = NO_CLIP_COLLISION_TYPE if terrain.no_clip else TERRAIN_COLLISION_TYPE
            self.space.add(body, shape)

    def add_boundaries(self):
        half_size = self.map_size // 2
        boundary_size = 500
        boundaries = [
            Terrain(Vec2d(0, -half_size - 250), Vec2d(self.map_size + 998, boundary_size), (128, 128, 128), "r", True, False),
            Terrain(Vec2d(0, half_size + 250), Vec2d(self.map_size + 998, boundary_size), (128, 128, 128), "r", True, False),
            Terrain(Vec2d(-half_size - 250, 0), Vec2d(boundary_size, self.map_size), (128, 128, 128), "r", True, False),
            Terrain(Vec2d(half_size + 250, 0), Vec2d(boundary_size, self.map_size), (128, 128, 128), "r", True, False)
        ]
        self.add_terrain(boundaries)


app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    async def send_game_state(self, game_server):
        game_states = game_server.serialize_game_state()
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_bytes(game_states[session_id])
            except Exception as e:
                print(f"Error sending game state to session id {session_id}: {e}")

class GameServer:
    def __init__(self):
        self.game = Game()
        self.manager = ConnectionManager()
        self.send_game_state_task = None

    def start(self):
        print("Server up and running")
        self.game.map_size = 6000
        self.game.add_boundaries()

        threading.Thread(target=self.game.check_player_timeout, daemon=True).start()

        while True:
            self.game.update_physics(1 / 60.0)
            time.sleep(1 / 60.0)

    async def send_game_state_periodically(self):
        while True:
            await asyncio.sleep(1 / SEND_INTERVAL)
            await self.manager.send_game_state(self.game)

@app.on_event("startup")
async def startup_event():
    
    game_server = GameServer()
    app.state.game_server = game_server

    threading.Thread(target=game_server.start, daemon=True).start()

    game_server.send_game_state_task = asyncio.create_task(game_server.send_game_state_periodically())
    async def pullpush_player_data_periodically():
        while True:
            await asyncio.sleep(5)
            with game_server.game.lock:

                for session_id, player in game_server.game.players.items():
                    player_data = collection.find_one({"player_id": player.player_id})
                    if player_data:
                        player.name = player_data["name"]
                        player.color = game_pb2.Color(r=player_data["color"][0], g=player_data["color"][1], b=player_data["color"][2])

                for session_id, player in game_server.game.players.items():
                    collection.update_one(
                        {"player_id": player.player_id},
                        {"$set": {
                            "position": player.body.position,
                            "hp": player.hp,
                            "max_hp": player.max_hp,
                            "hp_regen_rate": player.hp_regen_rate,
                            "last_hit": player.last_hit,
                            "dead": player.dead
                        }},
                        upsert=True
                    )

    asyncio.create_task(pullpush_player_data_periodically())

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    url = 'http://auth-server:8002/verify'
    auth_pack = {'session_id': session_id}
    response = requests.post(url, json=auth_pack)
    print("Session ID: ", session_id)

    pid = response.json().get('player_id')
    if session_id in app.state.game_server.manager.active_connections:
        await websocket.accept()
        await websocket.close(code=1008, reason="Session ID already connected")
    elif pid:
        game_server = app.state.game_server
        await game_server.manager.connect(websocket, session_id)

        try:
            while True:
                data = await websocket.receive_bytes()
                game_server.game.process_input(data, websocket.client, session_id, pid)
        except WebSocketDisconnect:
            game_server.manager.disconnect(session_id)
            print(f"Session {session_id} disconnected")
    else:
        await websocket.accept()
        await websocket.close(code=1008, reason="Invalid session ID")

if __name__ == "__main__":
    client = MongoClient("mongodb://mongo:27017/")
    db = client.game

    collection = db.game_state
    uvicorn.run(app, host="0.0.0.0", port=8000)
