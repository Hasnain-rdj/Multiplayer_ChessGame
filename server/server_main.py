import socket
import threading
import time
from common.protocol import make_message, parse_message
from common.chess_game import ChessGame

HOST = '0.0.0.0'
PORT = 5555
clients = []
players = []  # List of (client_socket, addr, name, color)
game = ChessGame()

# Add time control (e.g., 5 minutes per player)
TIME_LIMIT_SECONDS = 5 * 60  # 5 minutes
player_times = {'white': TIME_LIMIT_SECONDS, 'black': TIME_LIMIT_SECONDS}
last_move_time = None
current_timer_color = None

# Broadcast message to all clients
def broadcast(message, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.sendall(message)
            except Exception:
                pass

def handle_client(client_socket, addr):
    global players, player_times, last_move_time, current_timer_color
    print(f"Client connected: {addr}")
    # Receive player name
    try:
        name_data = client_socket.recv(1024)
        name_msg = parse_message(name_data.decode())
        if name_msg['type'] == 'join':
            player_name = name_msg['content'].get('name', f"Player_{len(players)+1}")
        else:
            player_name = f"Player_{len(players)+1}"
    except Exception:
        player_name = f"Player_{len(players)+1}"
    # Assign color
    if len(players) == 0:
        color = 'white'
    elif len(players) == 1:
        color = 'black'
    elif len(players) == 2:
        color= 'spectator'
    else:
        # More than 2 players: spectator mode (not implemented yet)
        client_socket.sendall(make_message('error', {'text': 'Game is full. Only two players allowed.'}))
        client_socket.close()
        return
    players.append((client_socket, addr, player_name, color))
    clients.append(client_socket)
    # Notify client of their color
    client_socket.sendall(make_message('color', {'color': color}))
    print(f"Assigned {player_name} as {color}")
    # If both players are connected, broadcast a board message to start the game
    if len(players) == 2:
        last_move_time = time.time()
        current_timer_color = 'white'
        board_msg = make_message('board', {
            'fen': game.get_board_fen(),
            'move': None,
            'turn': game.turn,
            'history': game.get_move_history(),
            'game_over': game.is_game_over(),
            'winner': game.get_winner(),
            'both_connected': True,
            'player_times': player_times
        })
        broadcast(board_msg)
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            try:
                msg_obj = parse_message(data.decode())
                if msg_obj['type'] == 'chat':
                    sender = player_name
                    chat_msg = make_message('chat', {'sender': sender, 'text': msg_obj['content'].get('text', '')})
                    broadcast(chat_msg, sender=client_socket)
                    print(f"{sender}: {msg_obj['content'].get('text', '')}")
                elif msg_obj['type'] == 'move':
                    move_uci = msg_obj['content'].get('move')
                    sender = player_name
                    # Only allow move if it's this player's turn and color
                    if (color == 'white' and game.turn == 'white') or (color == 'black' and game.turn == 'black'):
                        now = time.time()
                        # Update timer for the player who just moved
                        if current_timer_color == color and last_move_time is not None:
                            elapsed = now - last_move_time
                            player_times[color] -= elapsed
                            if player_times[color] <= 0:
                                # Time out, other player wins
                                winner = 'black' if color == 'white' else 'white'
                                board_msg = make_message('board', {
                                    'fen': game.get_board_fen(),
                                    'move': move_uci,
                                    'turn': game.turn,
                                    'history': game.get_move_history(),
                                    'game_over': True,
                                    'winner': winner,
                                    'player_times': player_times
                                })
                                broadcast(board_msg)
                                break
                        last_move_time = now
                        current_timer_color = 'black' if color == 'white' else 'white'
                        if move_uci and game.push_move(move_uci):
                            board_msg = make_message('board', {
                                'fen': game.get_board_fen(),
                                'move': move_uci,
                                'turn': game.turn,
                                'history': game.get_move_history(),
                                'game_over': game.is_game_over(),
                                'winner': game.get_winner(),
                                'player_times': player_times
                            })
                            broadcast(board_msg)
                            print(f"Move {move_uci} accepted from {sender}")
                        else:
                            error_msg = make_message('error', {'text': f'Illegal move: {move_uci}'})
                            client_socket.sendall(error_msg)
                    else:
                        error_msg = make_message('error', {'text': 'Not your turn or wrong color.'})
                        client_socket.sendall(error_msg)
                else:
                    broadcast(data, sender=client_socket)
            except Exception as e:
                print(f"Error parsing message from {addr}: {e}")
    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        print(f"Client disconnected: {addr}")
        clients.remove(client_socket)
        for i, (sock, _, _, _) in enumerate(players):
            if sock == client_socket:
                players.pop(i)
                break
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"Server listening on {HOST}:{PORT}")
    try:
        while True:
            client_socket, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Shutting down server.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
