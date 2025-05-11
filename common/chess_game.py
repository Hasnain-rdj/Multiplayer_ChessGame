import chess
import chess.engine

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.turn = 'white'  # or 'black'
        self.winner = None
        self.move_history = []

    def is_legal_move(self, move_uci):
        try:
            move = chess.Move.from_uci(move_uci)
            return move in self.board.legal_moves
        except Exception:
            return False

    def push_move(self, move_uci):
        if self.is_legal_move(move_uci):
            move = chess.Move.from_uci(move_uci)
            self.board.push(move)
            self.move_history.append(move_uci)
            if self.board.is_checkmate():
                self.winner = 'white' if self.turn == 'black' else 'black'
            self.turn = 'black' if self.turn == 'white' else 'white'
            return True
        return False

    def get_board_fen(self):
        return self.board.fen()

    def get_move_history(self):
        return self.move_history

    def is_game_over(self):
        return self.board.is_game_over()

    def get_winner(self):
        return self.winner
