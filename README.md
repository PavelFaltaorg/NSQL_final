# Multiplayer Game Backend + Front

Repo for a multiplayer game featuring a server-client architecture using arcade, FastAPI and WebSockets. The game uses protocol buffers (`game.proto`) for serializing player inputs and synchronizing game state.
## Features

- **FastAPI Server:** Handles player connections and broadcasts game state updates.
- **WebSocket Client:** Uses arcade for rendering, connects to the FastAPI server to receive updates and send player input.
- **Protocol Buffers:** Used for efficient serialization of game data (`game.proto`).

## Requirements

- Python 3.11 (tested on 3.11.2)

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/multiplayer-game-backend.git
   cd multiplayer-game-backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows, use 'venv\Scripts\activate'
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server:**
   ```bash
   python server.py
   ```

5. **Run the client:**
   ```bash
   python client.py
   ```

## Game Protocol

The game uses a protocol buffer defined in `game.proto` for encoding player inputs and server responses. You can regenerate the Python code for the protobuf using:

```bash
protoc --python_out=. game.proto
```
