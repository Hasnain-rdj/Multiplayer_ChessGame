import socket
import threading
import pygame
import sys
import queue
import os
import tkinter as tk
from tkinter import simpledialog, messagebox
from common.protocol import make_message, parse_message
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuration
default_server_ip = '16.171.152.161'
default_server_port = 5555

# GUI settings
WINDOW_WIDTH, WINDOW_HEIGHT = 960, 720
BOARD_SIZE = 640
CHAT_HEIGHT = 80
FONT_SIZE = 24

# Thread-safe queue for incoming messages
gui_message_queue = queue.Queue()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)

# Connect to server
def connect_to_server(ip, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((ip, port))
        print(f"Connected to server at {ip}:{port}")
        return client_socket
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                gui_message_queue.put("Disconnected from server.")
                break
            msg_obj = parse_message(data.decode())
            if msg_obj['type'] == 'chat':
                gui_message_queue.put(f"{msg_obj['content'].get('sender', 'Server')}: {msg_obj['content'].get('text', '')}")
            else:
                gui_message_queue.put(data.decode())
        except Exception as e:
            gui_message_queue.put(f"Error receiving: {e}")
            break

def draw_board(screen, board_fen=None, selected_square=None, legal_moves=None, flipped=False):
    import chess
    square_size = BOARD_SIZE // 8
    king_in_check_square = None
    if board_fen:
        board = chess.Board(board_fen)
        if board.is_check():
            # Find the king of the side to move
            king_color = board.turn
            king_square = board.king(king_color)
            king_in_check_square = king_square
    for row in range(8):
        for col in range(8):
            draw_col = col if not flipped else 7 - col
            draw_row = row if not flipped else 7 - row
            color = LIGHT_BROWN if (draw_row + draw_col) % 2 == 0 else DARK_BROWN
            square = chess.square(col, 7 - row)
            # Highlight selected square
            if selected_square == square:
                color = (255, 255, 0)
            # Highlight legal moves
            if legal_moves and square in legal_moves:
                color = (120, 200, 120)
            # Highlight king in check
            if king_in_check_square is not None and square == king_in_check_square:
                color = (255, 120, 120)  # light red
            pygame.draw.rect(screen, color, (draw_col * square_size, draw_row * square_size, square_size, square_size))
    if board_fen:
        piece_map = {
            'K': 'Chess_klt60.png', 'Q': 'Chess_qlt60.png', 'R': 'Chess_rlt60.png', 'B': 'Chess_blt60.png', 'N': 'Chess_nlt60.png', 'P': 'Chess_plt60.png',
            'k': 'Chess_kdt60.png', 'q': 'Chess_qdt60.png', 'r': 'Chess_rdt60.png', 'b': 'Chess_bdt60.png', 'n': 'Chess_ndt60.png', 'p': 'Chess_pdt60.png',
        }
        asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
        if not hasattr(draw_board, 'piece_images'):
            piece_images = {}
            for symbol, fname in piece_map.items():
                img_path = os.path.join(asset_dir, fname)
                if os.path.exists(img_path):
                    img = pygame.image.load(img_path)
                    img = pygame.transform.smoothscale(img, (square_size, square_size))
                    piece_images[symbol] = img
            draw_board.piece_images = piece_images
        else:
            piece_images = draw_board.piece_images
        board = chess.Board(board_fen)
        for i in range(64):
            piece = board.piece_at(i)
            if piece:
                p = piece.symbol()
                row, col = 7 - (i // 8), i % 8
                draw_col = col if not flipped else 7 - col
                draw_row = row if not flipped else 7 - row
                if p in piece_images:
                    screen.blit(piece_images[p], (draw_col * square_size, draw_row * square_size))

def draw_chat_right(screen, font, chat_lines, input_text):
    chat_x = BOARD_SIZE + 10
    chat_y = 10
    chat_width = 300
    chat_height = WINDOW_HEIGHT - 20
    pygame.draw.rect(screen, GRAY, (BOARD_SIZE, 0, chat_width, WINDOW_HEIGHT))
    # Draw chat history with wrapping
    max_line_length = 36
    max_lines = (chat_height - 40) // FONT_SIZE
    wrapped_lines = []
    for line in chat_lines[-max_lines:]:
        while len(line) > max_line_length:
            wrapped_lines.append(line[:max_line_length])
            line = line[max_line_length:]
        wrapped_lines.append(line)
    for i, line in enumerate(wrapped_lines[-max_lines:]):
        txt_surface = font.render(line, True, BLACK)
        screen.blit(txt_surface, (chat_x, chat_y + i * FONT_SIZE))
    # Draw input text
    input_surface = font.render("> " + input_text, True, BLACK)
    screen.blit(input_surface, (chat_x, chat_y + chat_height - 30))

def gui_main(sock, player_color, player_name):
    import chess
    pygame.init()
    CHAT_WIDTH = 320
    screen = pygame.display.set_mode((BOARD_SIZE + CHAT_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"Chess - {player_name} ({player_color.title()})")
    font = pygame.font.SysFont(None, FONT_SIZE)
    clock = pygame.time.Clock()

    chat_lines = []
    input_text = ""
    input_active = True
    board_fen = chess.STARTING_FEN
    error_message = ""
    selected_square = None
    legal_moves = []
    board = chess.Board(board_fen)
    flipped = (player_color == 'black')
    promotion_pending = None
    promo_square = None
    promo_from = None
    game_over = False
    winner_name = None
    opponent_connected = False

    # Time logic
    player_times = {'white': 5*60, 'black': 5*60}  # default 5 min, will be updated from server
    last_update_time = time.time()
    active_timer = None

    def format_time(secs):
        mins = int(secs) // 60
        s = int(secs) % 60
        return f"{mins:02}:{s:02}"

    def get_piece_image(symbol):
        piece_map = {
            'Q': 'Chess_qlt60.png', 'R': 'Chess_rlt60.png', 'B': 'Chess_blt60.png', 'N': 'Chess_blt60.png',
            'q': 'Chess_qdt60.png', 'r': 'Chess_rdt60.png', 'b': 'Chess_bdt60.png', 'n': 'Chess_bdt60.png',
        }
        asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
        fname = piece_map[symbol]
        img_path = os.path.join(asset_dir, fname)
        img = pygame.image.load(img_path)
        img = pygame.transform.smoothscale(img, (48, 48))
        return img

    def reset_game():
        nonlocal board_fen, error_message, selected_square, legal_moves, board, promotion_pending, promo_square, promo_from, game_over, winner_name, opponent_connected
        board_fen = chess.STARTING_FEN
        error_message = ""
        selected_square = None
        legal_moves = []
        board = chess.Board(board_fen)
        promotion_pending = None
        promo_square = None
        promo_from = None
        game_over = False
        winner_name = None
        opponent_connected = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not game_over:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        if input_text.strip():
                            msg = make_message('chat', {'text': input_text})
                            sock.sendall(msg)
                            chat_lines.append(f"You: {input_text}")
                            input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        if len(input_text) < 60:
                            input_text += event.unicode
            elif event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                mouse_x, mouse_y = event.pos
                if not opponent_connected:
                    error_message = "Waiting for the opponent to join."
                    continue
                if promotion_pending:
                    promo_pieces = ['q', 'r', 'b', 'n']
                    for idx, p in enumerate(promo_pieces):
                        px = BOARD_SIZE + 40 + idx * 60
                        py = 100
                        if px <= mouse_x <= px+48 and py <= mouse_y <= py+48:
                            move = chess.Move(promo_from, promo_square, promotion={'q': chess.QUEEN, 'r': chess.ROOK, 'b': chess.BISHOP, 'n': chess.KNIGHT}[p])
                            move_uci = move.uci()
                            msg = make_message('move', {'move': move_uci})
                            sock.sendall(msg)
                            promotion_pending = None
                            promo_square = None
                            promo_from = None
                            selected_square = None
                            legal_moves = []
                elif mouse_x < BOARD_SIZE and mouse_y < BOARD_SIZE:
                    col = mouse_x // (BOARD_SIZE // 8)
                    row = 7 - (mouse_y // (BOARD_SIZE // 8))
                    if flipped:
                        col = 7 - col
                        row = 7 - row
                    square = chess.square(col, row)
                    board = chess.Board(board_fen)
                    if selected_square is None:
                        piece = board.piece_at(square)
                        if piece and ((board.turn and piece.color and player_color == 'white') or (not board.turn and not piece.color and player_color == 'black')):
                            selected_square = square
                            legal_moves = [move.to_square for move in board.legal_moves if move.from_square == square]
                    else:
                        if square in legal_moves:
                            if board.piece_at(selected_square).piece_type == chess.PAWN and (chess.square_rank(square) == 0 or chess.square_rank(square) == 7):
                                promotion_pending = True
                                promo_square = square
                                promo_from = selected_square
                            else:
                                move = chess.Move(selected_square, square)
                                move_uci = move.uci()
                                msg = make_message('move', {'move': move_uci})
                                sock.sendall(msg)
                                selected_square = None
                                legal_moves = []
                        else:
                            selected_square = None
                            legal_moves = []
        while not gui_message_queue.empty():
            msg = gui_message_queue.get()
            if msg.startswith('{'):
                try:
                    msg_obj = parse_message(msg)
                    if msg_obj['type'] == 'board':
                        board_fen = msg_obj['content'].get('fen', board_fen)
                        board = chess.Board(board_fen)
                        error_message = ""
                        selected_square = None
                        legal_moves = []
                        game_over = msg_obj['content'].get('game_over', False)
                        winner_name = msg_obj['content'].get('winner', None)
                        # Detect if both players are connected (if both white and black have joined)
                        if 'turn' in msg_obj['content']:
                            opponent_connected = True
                        # Update timers
                        if 'player_times' in msg_obj['content']:
                            player_times = msg_obj['content']['player_times']
                        if 'turn' in msg_obj['content']:
                            active_timer = msg_obj['content']['turn']
                        last_update_time = time.time()
                    elif msg_obj['type'] == 'error':
                        error_message = msg_obj['content'].get('text', '')
                    elif msg_obj['type'] == 'chat':
                        chat_lines.append(f"{msg_obj['content'].get('sender', 'Server')}: {msg_obj['content'].get('text', '')}")
                except Exception:
                    chat_lines.append(msg)
            else:
                chat_lines.append(msg)
        # Timer update (client-side smooth display)
        now = time.time()
        if active_timer and not game_over and opponent_connected:
            if player_times[active_timer] > 0:
                elapsed = now - last_update_time
                # Only update the timer for the active player
                show_times = player_times.copy()
                show_times[active_timer] = max(0, player_times[active_timer] - elapsed)
            else:
                show_times = player_times.copy()
        else:
            show_times = player_times.copy()
        # Draw everything
        screen.fill(WHITE)
        draw_board(screen, board_fen, selected_square, legal_moves, flipped)
        draw_chat_right(screen, font, chat_lines, input_text)
        # Draw timers (both at the bottom)
        timer_font = pygame.font.SysFont(None, 36)
        # Show your timer and opponent's timer side by side at the bottom
        if player_color == 'white':
            my_time = show_times['white']
            opp_time = show_times['black']
            my_label = "Your Time"
            opp_label = "Opponent Time"
        else:
            my_time = show_times['black']
            opp_time = show_times['white']
            my_label = "Your Time"
            opp_label = "Opponent Time"
        # Draw a white rectangle at the bottom for timers
        pygame.draw.rect(screen, WHITE, (0, BOARD_SIZE, BOARD_SIZE, WINDOW_HEIGHT - BOARD_SIZE))
        my_time_surface = timer_font.render(f"{my_label}: {format_time(my_time)}", True, (0,0,0))
        opp_time_surface = timer_font.render(f"{opp_label}: {format_time(opp_time)}", True, (0,0,0))
        # Center both timers horizontally at the bottom
        total_width = my_time_surface.get_width() + 40 + opp_time_surface.get_width()
        start_x = (BOARD_SIZE - total_width) // 2
        y_pos = BOARD_SIZE + 20
        screen.blit(my_time_surface, (start_x, y_pos))
        screen.blit(opp_time_surface, (start_x + my_time_surface.get_width() + 40, y_pos))
        if promotion_pending:
            promo_pieces = ['q', 'r', 'b', 'n']
            for idx, p in enumerate(promo_pieces):
                img = get_piece_image(p.upper() if player_color == 'white' else p)
                px = BOARD_SIZE + 40 + idx * 60
                py = 100
                screen.blit(img, (px, py))
        # Show waiting message in the bottom white area if opponent not connected
        if not opponent_connected and not game_over:
            # Only show the waiting message if the game hasn't started (i.e., both players not connected)
            wait_surface = font.render("Waiting for the opponent to join...", True, (0,0,200))
            pygame.draw.rect(screen, WHITE, (0, BOARD_SIZE, BOARD_SIZE, WINDOW_HEIGHT - BOARD_SIZE))
            screen.blit(wait_surface, (20, BOARD_SIZE + 20))
        # Only show error_message if it's not the waiting-for-opponent message and opponent is connected
        if error_message and (opponent_connected or error_message != "Waiting for the opponent to join."):
            err_surface = font.render(error_message, True, (200,0,0))
            screen.blit(err_surface, (10, BOARD_SIZE - 60))
        if game_over:
            end_text = f"{winner_name} Won the game! Press 'R' to reset." if winner_name else "Draw! Press 'R' to reset."
            end_surface = font.render(end_text, True, (0, 128, 0))
            screen.blit(end_surface, (BOARD_SIZE//2 - 120, BOARD_SIZE//2 - 20))
        pygame.display.flip()
        clock.tick(30)
    sock.close()
    pygame.quit()
    sys.exit()

def show_help_window(parent):
    import tkinter as tk
    from tkinter import Toplevel, Label, Button, PhotoImage
    import os
    help_win = Toplevel(parent)
    help_win.title("Chess Rules & Pieces")
    help_win.geometry("600x600")
    help_win.configure(bg="#f0e6d2")
    Label(help_win, text="Chess Rules", font=("Arial", 18, "bold"), bg="#f0e6d2").pack(pady=10)
    rules = (
        "1. The game is played between two players, White and Black.\n"
        "2. White moves first, then players alternate turns.\n"
        "3. The goal is to checkmate the opponent's king.\n"
        "4. Each piece moves in a unique way.\n"
        "5. Special moves: castling, en passant, pawn promotion.\n"
        "6. The game ends in checkmate, stalemate, or draw.\n"
    )
    Label(help_win, text=rules, font=("Arial", 12), bg="#f0e6d2", justify="left").pack(pady=5)
    Label(help_win, text="Pieces:", font=("Arial", 14, "bold"), bg="#f0e6d2").pack(pady=10)
    # Piece descriptions
    piece_info = [
        ("King", "Moves one square in any direction.", "Chess_klt60.png"),
        ("Queen", "Moves any number of squares in any direction.", "Chess_qlt60.png"),
        ("Rook", "Moves any number of squares horizontally or vertically.", "Chess_rlt60.png"),
        ("Bishop", "Moves any number of squares diagonally.", "Chess_blt60.png"),
        ("Knight", "Moves in an 'L' shape: two squares in one direction, then one at a right angle.", "Chess_nlt60.png"),
        ("Pawn", "Moves forward one square, captures diagonally, promotes on last rank.", "Chess_plt60.png"),
    ]
    asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
    for name, desc, img_file in piece_info:
        frame = tk.Frame(help_win, bg="#f0e6d2")
        frame.pack(anchor="w", padx=30, pady=2)
        img_path = os.path.join(asset_dir, img_file)
        if os.path.exists(img_path):
            try:
                img = PhotoImage(file=img_path)
                img = img.subsample(2,2)
                lbl_img = Label(frame, image=img, bg="#f0e6d2")
                lbl_img.image = img
                lbl_img.pack(side="left")
            except Exception:
                Label(frame, text="[img]", bg="#f0e6d2").pack(side="left")
        else:
            Label(frame, text="[img]", bg="#f0e6d2").pack(side="left")
        Label(frame, text=f"  {name}: {desc}", font=("Arial", 12), bg="#f0e6d2").pack(side="left")
    Button(help_win, text="Back", font=("Arial", 12), command=help_win.destroy, bg="#d2b48c").pack(pady=20)
    help_win.transient(parent)
    help_win.grab_set()
    parent.wait_window(help_win)

def get_connection_info():
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.title("Welcome to Chess")
    root.geometry("480x350")
    root.configure(bg="#f0e6d2")
    # Greeting
    tk.Label(root, text="Hello Chess Master!!", font=("Arial", 20, "bold"), bg="#f0e6d2").pack(pady=10)
    tk.Label(root, text="Welcome to the Real-Time Multiplayer Chess Game", font=("Arial", 13), bg="#f0e6d2").pack(pady=5)
    # Form
    form = tk.Frame(root, bg="#f0e6d2")
    form.pack(pady=20)
    tk.Label(form, text="Server IP:", font=("Arial", 12), bg="#f0e6d2").grid(row=0, column=0, sticky="e", pady=5)
    ip_entry = tk.Entry(form, font=("Arial", 12))
    ip_entry.grid(row=0, column=1, pady=5)
    ip_entry.insert(0, default_server_ip)
    tk.Label(form, text="Port:", font=("Arial", 12), bg="#f0e6d2").grid(row=1, column=0, sticky="e", pady=5)
    port_entry = tk.Entry(form, font=("Arial", 12))
    port_entry.grid(row=1, column=1, pady=5)
    port_entry.insert(0, str(default_server_port))
    tk.Label(form, text="Your Name:", font=("Arial", 12), bg="#f0e6d2").grid(row=2, column=0, sticky="e", pady=5)
    name_entry = tk.Entry(form, font=("Arial", 12))
    name_entry.grid(row=2, column=1, pady=5)
    # Buttons
    btn_frame = tk.Frame(root, bg="#f0e6d2")
    btn_frame.pack(pady=10)
    def on_connect():
        ip = ip_entry.get().strip()
        port = port_entry.get().strip()
        name = name_entry.get().strip()
        if not ip or not port or not name:
            messagebox.showerror("Error", "All fields are required.")
            return
        try:
            port_int = int(port)
        except ValueError:
            messagebox.showerror("Error", "Port must be a number.")
            return
        root.destroy()
        nonlocal_ip[0] = ip
        nonlocal_port[0] = port_int
        nonlocal_name[0] = name
    def on_help():
        show_help_window(root)
    connect_btn = tk.Button(btn_frame, text="Connect", font=("Arial", 13, "bold"), bg="#b8e994", command=on_connect, width=10)
    connect_btn.pack(side="left", padx=10)
    help_btn = tk.Button(btn_frame, text="Help", font=("Arial", 13), bg="#d2b48c", command=on_help, width=10)
    help_btn.pack(side="left", padx=10)
    # Focus
    name_entry.focus()
    # Store values
    nonlocal_ip = [None]
    nonlocal_port = [None]
    nonlocal_name = [None]
    root.mainloop()
    if not (nonlocal_ip[0] and nonlocal_port[0] and nonlocal_name[0]):
        sys.exit(0)
    return nonlocal_ip[0], nonlocal_port[0], nonlocal_name[0]

def main():
    ip, port, player_name = get_connection_info()
    sock = connect_to_server(ip, port)
    if not sock:
        return
    # Send player name to server
    join_msg = make_message('join', {'name': player_name})
    sock.sendall(join_msg)
    # Receive color assignment
    color_msg = sock.recv(1024)
    color_info = parse_message(color_msg.decode())
    if color_info['type'] == 'color':
        player_color = color_info['content']['color']
    else:
        print("Failed to get color assignment from server.")
        return
    # Start thread to receive messages
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()
    # Start GUI
    gui_main(sock, player_color, player_name)

if __name__ == "__main__":
    main()
