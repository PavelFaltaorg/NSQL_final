import arcade
import threading
from typing import Dict, Set, List
import arcade.color
import arcade.color
import arcade.color
import arcade.color
import pymunk
from time import time
from datetime import datetime
from pymunk import Vec2d
import numpy as np
import imgui
from coolname import generate
from Game_server.code.client_classes import Player, Bullet, Terrain, GameState, Entity, ChatWindow, Minimap, GUI
import random
import asyncio
import websockets
import Game_server.code.game_pb2 as game_pb2
import zstandard as zstd
from collections import deque
from time import time_ns


SERVER_ADDRESS = ('localhost', 12345)
SEND_UPDATE_INTERVAL = 1 / 60.0
FPS = 60 
SCREEN = pymunk.Vec2d(1000, 1000)

MINIMAP_WIDTH = 250
MINIMAP_HEIGHT = 250

class NetworkManager:
    def __init__(self, game, session_id):
        self.game = game
        self.uri = f"ws://localhost:8000/ws/{session_id}"
        self.cctx = zstd.ZstdDecompressor()
        self.running = True
        self.server_fps = 1
        self.ping_deque = deque([0],maxlen=20)
        self.connection_lost = True
        self.pulse_alpha = 0
        self.pulse_direction = 1

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    print(f"Connection established with server at {self.uri}")
                    await asyncio.gather(self.send_input(websocket), self.receive_game_state(websocket))
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Server cannot be reached, another attempt in 5 seconds...")
                self.ping_deque.append(9999)
                await asyncio.sleep(5)
                

    async def send_input(self, websocket):
        while self.running:
            input_state = self.game.input_state
            mes = self.game.chat.get_string_message()
            input_state.message = ""
            if mes:
                input_state.message = mes

            try:
                await websocket.send(input_state.SerializeToString())
                input_state.respawn = False
            except websockets.ConnectionClosed:
                #print("Connection closed while sending input.")
                break
            except Exception as e:
                print(f"Error sending input: {e}")

            await asyncio.sleep(SEND_UPDATE_INTERVAL)

    async def receive_game_state(self, websocket):
        while self.running:
            try:
                data = await websocket.recv()
                decompressed_data = self.cctx.decompress(data)
                new_game_state = game_pb2.GameState()
                new_game_state.ParseFromString(decompressed_data)

                self.game.game_state = new_game_state

                if self.connection_lost:
                    if not self.pulse_alpha <= 10:
                        self.pulse_alpha += self.pulse_direction * 3
                        if self.pulse_alpha >= 150 or self.pulse_alpha <= 0:
                            self.pulse_direction *= -1
                    else:
                        self.connection_lost = False
                        self.pulse_alpha = 0
                        self.pulse_direction = 1

                self.ping_deque.append(int(abs(time_ns() - new_game_state.timestamp) / 1_000_000))
                self.game.update_entity_buffers(new_game_state)
                if new_game_state.HasField("message"):
                    self.game.chat.add_message(new_game_state.message)

                if new_game_state.server_fps != self.server_fps:
                    self.server_fps = new_game_state.server_fps

            except websockets.ConnectionClosed as e:
                print(f"Game State not received: {e.reason}")
                self.connection_lost = True
                break
            except Exception as e:
                print(f"Error receiving game state: {e}")

    def stop(self):
        self.running = False



class MyGame(arcade.Window):
    def __init__(self, session_id):
        super().__init__(SCREEN.x, SCREEN.y, "Arcade Game", resizable=True, vsync=True)
        arcade.set_background_color(arcade.color.AMAZON)

        self.keys: Set[int] = set()
        self.players: Dict[str, Player] = {}
        self.bullets: Dict[str, Bullet] = {}
        self.terrain: Terrain = Terrain()
        self.game_state = GameState()

        self.player_list = arcade.SpriteList()
        self.text_sprite_list = arcade.SpriteList()
        self.health_bars = arcade.SpriteList()
        self.health_bar_backgrounds = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        self.current_camera_pos = pymunk.Vec2d(1000, 0)

        self.input_state = game_pb2.PlayerInput()

        self.session_id = session_id
        self.input_state.session_id = session_id

        self.set_update_rate(1 / FPS)

        self.game_camera = arcade.Camera(self.width, self.height)
        self.gui_camera = arcade.Camera(self.width, self.height)

        self.mouse_x = 0
        self.mouse_y = 0

        self.initial_connection_made = False

        self.minimap = Minimap(MINIMAP_WIDTH, MINIMAP_HEIGHT, self.session_id)

        self.chat = ChatWindow()

        self.gui = GUI(self)

        self.network_manager = NetworkManager(self, session_id)

        self.asyncio_thread = threading.Thread(target=self.start_asyncio_loop, daemon=True)
        self.asyncio_thread.start()
    
    def start_asyncio_loop(self):
        asyncio.run(self.network_manager.connect()) 

    def update_input(self, dt: float):
        current_direction = pymunk.Vec2d(0, 0)
        target_position = pymunk.Vec2d(self.mouse_x, self.mouse_y) + self.game_camera.position

        if not imgui.is_any_item_active():
            if arcade.key.W in self.keys:
                current_direction += pymunk.Vec2d(0, 1)
            if arcade.key.S in self.keys:
                current_direction += pymunk.Vec2d(0, -1)
            if arcade.key.A in self.keys:
                current_direction += pymunk.Vec2d(-1, 0)
            if arcade.key.D in self.keys:
                current_direction += pymunk.Vec2d(1, 0)

        self.input_state.direction_x = current_direction.x
        self.input_state.direction_y = current_direction.y
        self.input_state.target_position_x = target_position.x
        self.input_state.target_position_y = target_position.y


    def on_update(self, dt: float):
        game_state_copy = self.game_state
        self.update_game_state(game_state_copy)
        self.update_camera()

    def setup_on_first_connection(self, game_state):
        if game_state.map_size > 0:
            self.terrain.add_bounding_terrain(game_state.map_size)
            self.initial_connection_made = True
            player = next((p for p in game_state.players if p.id == self.session_id), None)


    def setup(self):
        arcade.schedule(self.update_input, SEND_UPDATE_INTERVAL)
        arcade.schedule(self.update_displays, 1 / 2)

        self.tray_background = arcade.SpriteSolidColor(self.width, 30, (0, 0, 0, 180))
        self.tray_background.center_x = self.width // 2
        self.tray_background.center_y = self.height - 15

        self.ms_display = arcade.Text("", 0, 0, color=arcade.color.GHOST_WHITE, bold=True)
        self.time_display = arcade.Text("", 0, 0, color=arcade.color.GHOST_WHITE, bold=True)

    def update_displays(self, dt):
        value = np.mean(np.array(self.network_manager.ping_deque))
        if np.isnan(value):
            self.network_manager.ping_deque.append(9999)
        self.ms_display.text = f"{value:.0f}ms"
        self.time_display.text = datetime.now().strftime("%H:%M:%S")

    def on_resize(self, width, height):
        super().on_resize(width, height)

        self.tray_background.center_y = height - 15
        self.tray_background.center_x = width // 2
        self.tray_background.width = width
        self.ms_display.y = height - 20
        self.ms_display.x = 5
        self.time_display.y = height - 20
        self.time_display.x = width - 70

        self.game_camera.resize(width, height)
        self.gui_camera.resize(width, height)

    def on_draw(self):
        self.clear()

        self.game_camera.use()
        self.bullet_list.draw()
        self.player_list.draw()
        self.terrain.shape.draw()

        self.text_sprite_list.draw()
        self.health_bar_backgrounds.draw()
        self.health_bars.draw()

        self.gui.draw()

    def draw_pulsating_background(self):
        if self.network_manager.connection_lost:
            self.network_manager.pulse_alpha += self.network_manager.pulse_direction * 3
            if self.network_manager.pulse_alpha >= 150 or self.network_manager.pulse_alpha <= 0:
                self.network_manager.pulse_direction *= -1
            arcade.draw_rectangle_filled(
                0,
                self.height - 15,
                140,
                30,
                (255, 0, 0, self.network_manager.pulse_alpha)
            )

    def on_key_press(self, key: int, modifiers: int):
        self.keys.add(key)

    def on_key_release(self, key: int, modifiers: int):
        self.keys.discard(key)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if not self.gui.gui_elements_hovered and not self.chat.is_hovered:
                self.input_state.shoot = True

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.input_state.shoot = False

    def update_game_state(self, game_state: GameState):
        if not self.initial_connection_made:
            self.setup_on_first_connection(game_state)

        self.update_entities(self.players, game_state.players)
        self.update_entities(self.bullets, game_state.bullets)

    def get_hp_bar_color(self, hp, max):
        if hp > 0:
            diff = hp / max
            green = 255 * diff
            red = 255 - green
            return (red, green, 0)
        return (0, 0, 0)

    def update_entities(self, entity_dict: Dict[str, Entity], new_entities: List[Entity]):
        new_entity_dict = {e.id: e for e in new_entities}

        for e_id in list(entity_dict.keys()):
            if e_id not in new_entity_dict:
                entity_dict[e_id].shape.remove_from_sprite_lists()
                if isinstance(entity_dict[e_id], Player):
                    self.remove_text_sprite(e_id)
                    self.remove_health_bar(e_id)
                del entity_dict[e_id]

        for e in new_entity_dict.values():
            if e.id not in entity_dict:
                entity_dict[e.id] = self.create_entity(e)
            else:
                entity = entity_dict[e.id]
                entity.update_position(1 / FPS, FPS, self.network_manager.server_fps)
                entity.update(e)

        for session_id, player in self.players.items():
            health_bar_background = next((hb for hb in self.health_bar_backgrounds if hb.session_id == session_id), None)
            health_bar = next((hb for hb in self.health_bars if hb.session_id == session_id), None)
            text_sprite = next((ts for ts in self.text_sprite_list if ts.session_id == session_id), None)

            if player and player.hp > 0:
                if health_bar_background and not health_bar_background.visible:
                    health_bar_background.visible = True
                if health_bar_background:
                    health_bar_background.left = player.shape.center_x - 31
                    health_bar_background.center_y = player.shape.center_y + 30

                if health_bar and not health_bar.visible:
                    health_bar.visible = True
                if health_bar:
                    health_bar.color = self.get_hp_bar_color(player.hp, player.max_hp)
                    health_bar.width = 60 * player.hp / player.max_hp
                    health_bar.left = player.shape.center_x - 30
                    health_bar.center_y = player.shape.center_y + 30

                if text_sprite and not text_sprite.visible:
                    text_sprite.visible = True
                if text_sprite:
                    text_sprite.center_x = player.shape.center_x
                    text_sprite.center_y = player.shape.center_y + 50

                if player.id in new_entity_dict and player.name != new_entity_dict[player.id].name:
                    player.name = new_entity_dict[player.id].name
                    self.remove_text_sprite(player.id)
                    self.add_text_sprite(player.id, player)
            else:
                if health_bar_background:
                    health_bar_background.visible = False
                if health_bar:
                    health_bar.visible = False
                if text_sprite:
                    text_sprite.visible = False

    def remove_health_bar(self, session_id):
        for health_bar in self.health_bars:
            if health_bar.session_id == session_id:
                self.health_bars.remove(health_bar)
                break
        for health_bar_background in self.health_bar_backgrounds:
            if health_bar_background.session_id == session_id:
                self.health_bar_backgrounds.remove(health_bar_background)
                break

    def create_entity(self, entity_data: Entity):
        if isinstance(entity_data, game_pb2.Player):
            entity = Player(entity_data)
            self.player_list.append(entity.shape)
            self.players[entity_data.id] = entity

            next_position = pymunk.Vec2d(entity_data.x, entity_data.y) + pymunk.Vec2d(entity_data.vx, entity_data.vy) * (1 / FPS)
            entity.positions_buffer.append((time(), next_position))
            entity.position_at_receive = pymunk.Vec2d(entity_data.x, entity_data.y)

            self.add_text_sprite(entity_data.id, entity)
            self.add_health_bar(entity_data.id, entity)

        elif isinstance(entity_data, game_pb2.Bullet):
            entity = Bullet(entity_data)
            self.bullet_list.append(entity.shape)
            self.bullets[entity_data.id] = entity
    
            next_position = pymunk.Vec2d(entity_data.x, entity_data.y) + pymunk.Vec2d(entity_data.vx, entity_data.vy) * (1 / FPS)
            entity.positions_buffer.append((time(), next_position))
            entity.position_at_receive = pymunk.Vec2d(entity_data.x, entity_data.y)
            
        return entity

    def add_text_sprite(self, session_id, player):
        name_x = player.shape.center_x
        name_y = player.shape.center_y + 50
        text_sprite = arcade.create_text_sprite(
            player.name,
            name_x,
            name_y,
            arcade.color.BLACK if session_id == self.session_id else arcade.color.RED,
            14,
            anchor_x="center",
            bold=True
        )
        text_sprite.session_id = session_id
        self.text_sprite_list.append(text_sprite)

    def add_health_bar(self, session_id, player):
        health_bar = arcade.SpriteSolidColor(60, 10, arcade.color.WHITE)
        background = arcade.SpriteSolidColor(62, 12, arcade.color.BLACK)
        background.center_x = player.shape.center_x-1
        background.center_y = player.shape.center_y + 29
        background.session_id = session_id

        health_bar.center_x = player.shape.center_x
        health_bar.center_y = player.shape.center_y + 30
        health_bar.session_id = session_id

        self.health_bars.append(health_bar)
        self.health_bar_backgrounds.append(background)

    def remove_text_sprite(self, session_id):
        for text_sprite in self.text_sprite_list:
            if text_sprite.session_id == session_id:
                self.text_sprite_list.remove(text_sprite)
                break

    def update_entity_buffers(self, new_game_state: game_pb2.GameState):
        for player in new_game_state.players:
            if player.id in self.players:
                self.update_entity_buffer(self.players[player.id], player)

        for bullet in new_game_state.bullets:
            if bullet.id in self.bullets:
                self.update_entity_buffer(self.bullets[bullet.id], bullet)

    def update_entity_buffer(self, entity: Entity, data: Entity):
        entity.positions_buffer.append((time(), pymunk.Vec2d(data.x, data.y)))
        entity.position_at_receive = pymunk.Vec2d(entity.shape.position[0], entity.shape.position[1])

    def update_camera(self):
        if self.session_id in self.players:
            my_player = self.players[self.session_id]
            other_players = {id: player for id, player in self.players.items() if id != self.session_id and player.hp > 0}

            if my_player.hp > 0:
                fltr = [Vec2d(player.shape.position[0], player.shape.position[1])
                        for id, player in other_players.items()
                        if Vec2d(player.shape.position[0], player.shape.position[1]).get_distance(
                            Vec2d(my_player.shape.position[0], my_player.shape.position[1])) < min(self.width, self.height)]

                if fltr:
                    x = sum([i.x for i in fltr]) / len(fltr)
                    y = sum([i.y for i in fltr]) / len(fltr)
                    center = Vec2d(x, y)
                    target_camera_pos = (center + Vec2d(my_player.shape.position[0], my_player.shape.position[1])) / 2
                else:
                    target_camera_pos = my_player.shape.position
            else:
                if self.players.get(my_player.last_hit):
                    target_camera_pos = self.players[my_player.last_hit].shape.position
                else:
                    target_camera_pos = my_player.shape.position

            interpolation_speed = 0.05 
            target_offset = (target_camera_pos - pymunk.Vec2d(self.width, self.height) // 2)
            self.current_camera_pos += (target_offset - self.current_camera_pos) * interpolation_speed

            self.game_camera.move_to(self.current_camera_pos)

    def stop(self):
        self.network_manager.stop()

def start_game(session_id):
    game = MyGame(session_id=session_id)
    game.setup()
    try:
        arcade.run()
    finally:
        game.stop()

if __name__ == "__main__":
    SESSION_ID = "a2fdc8db-1d8a-4ba8-adbd-0fc377970d96"
    start_game(SESSION_ID)