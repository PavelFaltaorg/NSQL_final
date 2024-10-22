from collections import deque
from dataclasses import dataclass, field
from typing import List
import game_pb2
import arcade
import pymunk
import imgui
from arcade_imgui import ArcadeRenderer
from PIL import Image, ImageDraw
import OpenGL.GL as gl

PLAYER_RADIUS = 20
BULLET_RADIUS = 5


@dataclass
class GameState:
    players: List[game_pb2.Player] = field(default_factory=list)
    bullets: List[game_pb2.Bullet] = field(default_factory=list)
    map_size: int = 0
    timestamp: int = 0
    server_fps: int = 0
    leaderboard: List[game_pb2.LeaderboardEntry] = field(default_factory=list)


class Entity:
    def __init__(self, entity_data):
        self.id = entity_data.id
        self.shape = arcade.SpriteCircle(self.get_radius(), self.get_initial_color())
        self.shape.visible = False
        self.shape.position = (entity_data.x, entity_data.y)
        self.shape.session_id = entity_data.id
        self.positions_buffer = deque(maxlen=30)
        self.velocity = pymunk.Vec2d(entity_data.vx, entity_data.vy)
        self.position_at_receive = pymunk.Vec2d(0, 0)
        self.u = 0
        self.inter_time = 1

    def get_radius(self):
        raise NotImplementedError

    def get_initial_color(self):
        raise NotImplementedError

    def update_position(self, dt: float, fps: int, server_fps: int):#TODO fixnout predelat idk proc to jitteruje furt a nefunguje mrdam na to
        if len(self.positions_buffer) >= 2:
            if not self.shape.visible:
                self.shape.visible = True

            t0, p0 = self.positions_buffer[0]
            t1, p1 = self.positions_buffer[1]

            # Calculate frames per update using server_fps, more stable than relying on t1-t0 fluctuations
            frames_per_update = fps / server_fps

            # Calculate the error and log interpolation status
            error = (p1 - self.position_at_receive)
            #print(f"interpolation n. {self.inter_time} pblen: {len(self.positions_buffer)} u: {self.u} error: {error.length}, server_fps: {server_fps}")

            interpolated_position = arcade.lerp(p0, p1, self.u)
            self.shape.position = interpolated_position
            self.inter_time += 1

            # Increment u for interpolation progress
            self.u += 1 / frames_per_update

            # Handle position updates when u exceeds 1 (interpolation complete)
            if self.u >= 1:
                if len(self.positions_buffer) >= 3:
                    # Shift to the next position if buffer has 3 positions
                    self.u = 0
                    self.inter_time = 1
                    self.positions_buffer.popleft()  # Remove the oldest position
                else:
                    # Extrapolate if we're waiting for a new packet
                    #print("Extrapolating\n\n\n")
                    extrapolated_position = p1 + self.velocity * dt - (error * self.u/2)  # Smoother error compensation
                    self.shape.position = extrapolated_position


    def update(self, entity_data):
        pass

class Player(Entity):
    def __init__(self, entity_data):
        self.name = entity_data.name
        self.hp = entity_data.hp
        self.max_hp = entity_data.max_hp
        self.last_hit = entity_data.last_hit
        super().__init__(entity_data)

    def get_radius(self):
        return PLAYER_RADIUS

    def get_initial_color(self):
        return arcade.color.WHITE

    def update(self, entity_data):
        self.hp = entity_data.hp
        self.max_hp = entity_data.max_hp
        self.last_hit = entity_data.last_hit
        self.velocity = pymunk.Vec2d(entity_data.vx, entity_data.vy)
        self.shape.color = (entity_data.color.r, entity_data.color.g, entity_data.color.b)

class Bullet(Entity):
    def __init__(self, entity_data):
        super().__init__(entity_data)
    def get_radius(self):
        return BULLET_RADIUS

    def get_initial_color(self):
        return arcade.color.BLACK

class Terrain:
    def __init__(self):
        self.shape = arcade.ShapeElementList()

    def add_bounding_terrain(self, map_size):
        width = 500
        color = (100,100,100,150)

        top = arcade.create_line(-map_size // 2 - width, map_size // 2 + width // 2,
                    map_size // 2 + width, map_size // 2 + width // 2,
                    color=color, line_width=width)
        bot = arcade.create_line(-map_size // 2 - width, -map_size // 2 - width // 2,
                    map_size // 2 + width, -map_size // 2 - width // 2,
                    color=color, line_width=width)
        left = arcade.create_line(-map_size // 2 - width // 2, map_size // 2 + width,
                    -map_size // 2 - width // 2, -map_size // 2 - width,
                    color=color, line_width=width)
        right = arcade.create_line(map_size // 2 + width // 2, map_size // 2 + width,
                    map_size // 2 + width // 2, -map_size // 2 - width,
                    color=color, line_width=width)

        self.shape.append(top)
        self.shape.append(bot)
        self.shape.append(left)
        self.shape.append(right)

class Message:
    def __init__(self, message):
        self.message = message

    def get_display_lines(self, wrap_width, prefix=""):
        words = self.message.split()
        lines = []
        current_line = ""
        prefix_length = imgui.calc_text_size(prefix)[0] if prefix else 0

        for word in words:
            while imgui.calc_text_size(word)[0] > wrap_width:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                split_point = len(word) // 2
                while imgui.calc_text_size(word[:split_point])[0] > wrap_width:
                    split_point -= 1
                lines.append(word[:split_point])
                word = word[split_point:]
            if imgui.calc_text_size(current_line + " " + word)[0] + (prefix_length if not lines else 0) <= wrap_width:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        return lines

class PlayerMessage(Message):
    def __init__(self, name, color, message):
        super().__init__(message)
        self.name = name
        self.color = color

    def get_display_lines(self, wrap_width):
        # Include the player name in the first line
        prefix = f"{self.name}: "
        return super().get_display_lines(wrap_width, prefix)

class Announcement(Message):
    def __init__(self, message, color):
        super().__init__(message)
        self.color = color

class ChatWindow:
    def __init__(self):
        self.chat_messages = []
        self.new_chat_message = ""  # The new chat message input field
        self.is_hovered = False
        self.old_number_of_messages = 0
        self.string_message_list = deque()
    
    def get_string_message(self):
        return self.string_message_list.popleft() if self.string_message_list else None

    def add_message(self, message):
        if message.type == 0:
            self.chat_messages.append(Announcement(message.content, color = (218/255, 165/255, 32/255)))
        elif message.type == 1:
            self.chat_messages.append(PlayerMessage(message.header, (message.color.r/255, message.color.g/255, message.color.b/255), message.content))

    def draw(self):
        self.is_hovered = False
        imgui.set_next_window_position(0, 500, imgui.FIRST_USE_EVER)  # Adjust position as needed
        imgui.begin("Chat", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)

        self.draw_chat_messages()
        self.draw_input_field()

        if imgui.is_window_hovered():
            self.is_hovered = imgui.is_window_hovered()

        imgui.end()

    def draw_chat_messages(self):
        imgui.begin_child("ChatMessages", width=300, height=200, border=True)
        draw_list = imgui.get_window_draw_list()
        message_y = imgui.get_cursor_screen_pos()[1]-7
        spacing = 8  # Adjust this value to change the space between messages
        wrap_width = 260  # Fixed wrap width

        for i, message in enumerate(self.chat_messages):
            lines = message.get_display_lines(wrap_width)
            message_height = sum(imgui.calc_text_size(line)[1] for line in lines) + 8  # Adjust wrap_width as needed
            message_pos = imgui.get_cursor_screen_pos()
            mouse_x, mouse_y = imgui.get_mouse_pos()
            is_hovered = message_pos[0] <= mouse_x <= message_pos[0] + 290 and message_pos[1] <= mouse_y <= message_pos[1] + message_height

            message_color = self.get_message_color(is_hovered, i)
            self.draw_message_background(draw_list, message_pos, message_y, message_height, message_color, i)

            first_line = True
            for line in lines:
                text_height = imgui.calc_text_size(line)[1]
                imgui.set_cursor_screen_pos((message_pos[0], message_y))  # Set cursor position for the text
                self.draw_message_content(message, line, first_line)
                first_line = False
                message_y += text_height

            if imgui.is_mouse_double_clicked(0):
                self.check_double_click(message, message_pos, message_y, message_height)

            message_y += spacing  # Move to the next message position, including spacing
            imgui.set_cursor_screen_pos((message_pos[0], message_y))  # Update cursor position for the next message

        if imgui.is_window_hovered():
            self.is_hovered = imgui.is_window_hovered()

        if not self.old_number_of_messages == len(self.chat_messages):
            imgui.set_scroll_here(1.0)
            self.old_number_of_messages = len(self.chat_messages)
        imgui.end_child()

    def draw_input_field(self):
        imgui.push_item_width(300)  # Set custom width for the input text
        if imgui.is_key_pressed(imgui.KEY_ENTER):
            if not imgui.is_item_focused():
                imgui.set_keyboard_focus_here()  # Set focus to the input text field when Enter is pressed
        changed, message = imgui.input_text("", self.new_chat_message, 256, imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        if changed:
            self.string_message_list.append(message)
            self.new_chat_message = ""
        imgui.pop_item_width()

    def get_message_color(self, is_hovered, index):
        if is_hovered:
            return (0.5, 0.5, 0.5, 0.5)  # Highlight color
        else:
            return (0, 0, 0, 0.2) if index % 2 == 0 else (0, 0, 0, 0.4)  # Alternate colors

    def draw_message_background(self, draw_list, message_pos, message_y, message_height, message_color, index):
        start_mod = 0
        end_mod = 0
        # if index == 0:
        #     start_mod = 10
        # elif index == len(self.chat_messages) - 1:
        #     end_mod = 10

        draw_list.add_rect_filled(message_pos[0] - 10, message_y - start_mod, message_pos[0] + 310, message_y + message_height + end_mod, imgui.get_color_u32_rgba(*message_color))

    def draw_message_content(self, message, line, first_line, y_offset=3):
        if isinstance(message, PlayerMessage):
            if first_line:
                imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + y_offset)
                imgui.text_colored(f"{message.name}: ", *message.color)
                imgui.same_line()
                imgui.text(line)
            else:
                imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + y_offset)
                imgui.text(line)
        else:
            imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + y_offset)
            imgui.text_colored(line, *message.color)

    def check_double_click(self, message, message_pos, message_y, message_height):
        mouse_x, mouse_y = imgui.get_mouse_pos()
        if message_pos[0] <= mouse_x <= message_pos[0] + 290 and message_pos[1] <= mouse_y <= message_pos[1] + message_height:
            self.new_chat_message = message.message

class Minimap:
    def __init__(self, width, height, session_id):
        self.width = width
        self.height = height
        self.texture_id = gl.glGenTextures(1)
        self.image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.session_id = session_id

    def scale_coordinates(self, x, y, map_width, map_height):
        scale_x = self.width / map_width
        scale_y = self.height / map_height
        scaled_x = x * scale_x + self.width / 2
        scaled_y = y * scale_y + self.height / 2
        return scaled_x, scaled_y

    def update(self, player_list, bullet_list, map_size):
        self.draw.rectangle([(0, 0), (self.width, self.height)], fill=(0, 0, 0, 0))

        for bullet in bullet_list:
            scaled_x, scaled_y = self.scale_coordinates(bullet.center_x, bullet.center_y, map_size, map_size)
            self.draw.point((scaled_x, scaled_y), fill=(0, 0, 0))

        for player in player_list:
            scaled_x, scaled_y = self.scale_coordinates(player.center_x, player.center_y, map_size, map_size)
            if player.session_id == self.session_id:
                self.draw.chord((scaled_x - 2, scaled_y - 2, scaled_x + 2, scaled_y + 2), 0, 360, fill=(0, 0, 0), outline=player.color)
            else:
                self.draw.ellipse((scaled_x - 2, scaled_y - 2, scaled_x + 2, scaled_y + 2), fill=player.color)

        minimap_texture = self.image.tobytes()
        width, height = self.image.size

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, minimap_texture)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


class GUI:
    def __init__(self, game):
        self.game = game
        imgui.create_context()
        self.renderer = ArcadeRenderer(game)
        self.color = [game.input_state.color.r / 255.0, game.input_state.color.g / 255.0, game.input_state.color.b / 255.0]
        self.gui_elements_hovered = False

    def draw(self):
        self.game.gui_camera.use()
        self.game.tray_background.draw()
        self.game.draw_pulsating_background()
        self.game.ms_display.draw()
        self.game.time_display.draw()

        self.draw_imgui()

        self.game.minimap.update(self.game.player_list, self.game.bullet_list, self.game.game_state.map_size)

    def draw_imgui(self):
        if self.game.initial_connection_made:
            self.gui_elements_hovered = False
            imgui.new_frame()

            imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, 0, 0, 0, 0.5)

            if self.game.players.get(self.game.session_id) and self.game.players.get(self.game.session_id).hp <= 0:
                imgui.set_next_window_collapsed(False)
                imgui.begin("Respawn", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE | imgui.WINDOW_NO_TITLE_BAR)
                if imgui.button("Respawn", width=130, height=65):
                    self.game.input_state.respawn = True
                imgui.end()

            imgui.set_next_window_position(734, 30, imgui.FIRST_USE_EVER)
            imgui.begin(f"Minimap", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)
            minimap_pos = imgui.get_cursor_screen_pos()

            imgui.image(self.game.minimap.texture_id, self.game.minimap.width, self.game.minimap.height, uv0=(0, 1), uv1=(1, 0))
            player = self.game.players.get(self.game.session_id)

            if player:
                position = player.shape.position  # Assuming player has a position attribute
                draw_list = imgui.get_window_draw_list()
                # Calculate the position to overlay the text
                text_pos_x = minimap_pos[0] - 5  # Adjust as needed
                text_pos_y = minimap_pos[1] + 240  # Adjust as needed
                draw_list.add_text(text_pos_x, text_pos_y, imgui.get_color_u32_rgba(1, 1, 1, 1), f"({position[0]:.0f}, {position[1]:.0f})")

            if imgui.is_window_hovered():
                self.gui_elements_hovered = True

            imgui.end()  # RGBA with alpha 0.5 for transparency

            imgui.set_next_window_position(502, 30, imgui.FIRST_USE_EVER)  # x, y coordinates

            # Begin a new window for the leaderboard
            imgui.begin("Leaderboard", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)

            # Display each player's score
            for pos, entry in enumerate(self.game.game_state.leaderboard, 1):
                if pos == 6:
                    imgui.text(f"...")
                    pos = "6+"

                # Display the position and points in white
                imgui.text(f"{pos},")

                # Push the entry color for the name
                imgui.same_line()
                imgui.push_style_color(imgui.COLOR_TEXT, entry.color.r / 255, entry.color.g / 255, entry.color.b / 255)
                imgui.text(entry.name)
                imgui.pop_style_color()

                # Display the points in white
                imgui.same_line()
                imgui.text(f": {entry.points}")

            # End the window
            if imgui.is_window_hovered():
                self.gui_elements_hovered = True
            imgui.end()
            # RGBA with alpha 0.5 for transparency

            imgui.set_next_window_position(0, 30, imgui.FIRST_USE_EVER)  # x, y coordinates
            # Color picker window
            imgui.begin("Customization Panel", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)
            changed, self.color = imgui.color_edit3("", *self.color)
            if changed:
                # Update the player color in the input state
                self.game.input_state.color.r = int(self.color[0] * 255)
                self.game.input_state.color.g = int(self.color[1] * 255)
                self.game.input_state.color.b = int(self.color[2] * 255)

            if imgui.core.is_any_item_hovered():
                self.gui_elements_hovered = True
            # Name changer
            changed, new_name = imgui.input_text("", self.game.input_state.name, 25, imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
            if changed:
                self.game.input_state.name = new_name

            if imgui.is_window_hovered():
                self.gui_elements_hovered = True

            imgui.end()

            self.game.chat.draw()

            imgui.pop_style_color()

            imgui.render()
            self.renderer.render(imgui.get_draw_data())
