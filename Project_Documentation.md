# Multiplayer Chess Game using Socket Programming

## Table of Contents
1. Introduction
2. Features
3. Project Structure
4. How It Works
5. Installation & Setup
6. Usage
7. Code Overview
    - Client
    - Server
    - Common
8. Protocol
9. Time Control Logic
10. Screenshots
11. Dependencies

---

## 1. Introduction
This project is a real-time multiplayer chess game built using Python and socket programming. It allows two players to play chess over a network, with a graphical interface powered by Pygame and Tkinter. The project demonstrates concepts of computer networking, concurrency, and GUI programming.

---

## 2. Features
- Real-time chess gameplay between two players over a network.
- Graphical chessboard and pieces using Pygame.
- In-game chat functionality.
- Move validation and game state management.
- User-friendly connection and help dialogs.
- Support for chess rules: castling, en passant, pawn promotion, check, and checkmate.
- Chess clock: Each player has a timer; lose on time is supported.

---

## 3. Project Structure
```
CN_LAB Project_Multiplayer Chess Game/
├── client/
│   ├── client_main.py
│   └── assets/
│       └── (chess piece images)
├── server/
│   └── server_main.py
├── common/
│   ├── chess_game.py
│   └── protocol.py
```

---

## 4. How It Works
- The server listens for incoming connections and manages the game state.
- Each client connects to the server, sends their name, and receives their assigned color (white/black).
- Players interact with a graphical chessboard, make moves, and chat.
- The server validates moves, updates the game state, and broadcasts updates to all clients.
- The game ends when checkmate, stalemate, draw, or time-out is detected.

---

## 5. Installation & Setup
### Prerequisites
- Python 3.10+
- Required Python packages: `pygame`, `python-chess`, `tkinter` (standard with Python)

### Install Dependencies
Open a terminal and run:
```
pip install pygame python-chess
```

---

## 6. Usage
### 1. Start the Server
```
cd server
python server_main.py
```
The server will listen on `0.0.0.0:5555` by default.

### 2. Start the Client(s)
```
cd client
python client_main.py
```
- Enter the server IP, port, and your name in the GUI dialog.
- Wait for another player to join.
- Play chess and chat in real-time.

---

## 7. Code Overview
### Client
- `client/client_main.py`: Handles the GUI, user input, networking, and communication with the server. Uses Pygame for the chessboard and Tkinter for dialogs. Displays both players' timers at the bottom of the screen.

### Server
- `server/server_main.py`: Manages client connections, assigns player colors, validates moves, maintains game state, tracks chess clocks, and broadcasts updates.

### Common
- `common/chess_game.py`: Contains the `ChessGame` class for managing the chessboard, move validation, and game state using `python-chess`.
- `common/protocol.py`: Defines the message protocol for communication between client and server using JSON.

---

## 8. Protocol
All communication between client and server uses JSON-encoded messages. Each message has a `type` and a `content` dictionary.

**Example:**
```json
{
  "type": "move",
  "content": {
    "move": "e2e4"
  }
}
```

**Message Types:**
- `join`: Sent by client to join the game.
- `color`: Sent by server to assign color.
- `move`: Sent by client to make a move.
- `board`: Sent by server to update board state and timers.
- `chat`: Chat messages.
- `error`: Error messages.

---

## 9. Time Control Logic
- Each player starts with a fixed amount of time (e.g., 5 minutes).
- The timer for the player whose turn it is counts down; it pauses when their move is sent and the other player's timer starts.
- If a player's time runs out, the other player is declared the winner and a win message is shown.
- Both timers are displayed side by side at the bottom of the screen in the white area.

---

## 10. Screenshots
*(Add screenshots of the GUI, connection dialog, and gameplay here)*

---

## 11. Dependencies
- [pygame](https://www.pygame.org/)
- [python-chess](https://python-chess.readthedocs.io/)
- [tkinter](https://docs.python.org/3/library/tkinter.html) (standard with Python)
