"""
GameController: single entry point for UI. Orchestrates board, state, moves, undo/redo.
No UI imports; receives and returns data only.
"""

from typing import Optional

from core.board import Board
from core.game_state import GameState, STARTING_FEN
from core.move import Move
from core.move_generator import get_legal_moves
from core.rules import get_game_status
from core.apply import apply_move, undo_move, UndoInfo


class GameController:
    """
    Orchestrates game state and rules. UI calls methods here and renders
    returned state. Optional: get_last_move(), get_clock_state()/set_clock_state().
    """

    def __init__(self) -> None:
        self._board = Board()
        self._game_state = GameState()
        self._undo_stack: list[tuple[Move, UndoInfo]] = []
        self._redo_stack: list[tuple[Move, UndoInfo]] = []
        self._last_move: Optional[Move] = None
        self._selected_square: Optional[tuple[int, int]] = None
        self.reset_to_fen(STARTING_FEN)

    def get_board(self) -> Board:
        return self._board

    def get_game_state(self) -> GameState:
        return self._game_state

    def get_legal_moves(self, from_square: Optional[tuple[int, int]] = None) -> list[Move]:
        return get_legal_moves(self._board, self._game_state, from_square)

    def get_status(self) -> str:
        return get_game_status(self._board, self._game_state)

    def get_last_move(self) -> Optional[Move]:
        return self._last_move

    def get_selected_square(self) -> Optional[tuple[int, int]]:
        return self._selected_square

    def select(self, square: tuple[int, int]) -> None:
        piece = self._board.get_piece_at(square[0], square[1])
        side = self._game_state.side_to_move
        if piece is not None and piece.color == side:
            self._selected_square = square
        else:
            self._selected_square = None

    def clear_selection(self) -> None:
        self._selected_square = None

    def make_move(self, move: Move) -> bool:
        legal = self.get_legal_moves(move.from_square)
        if move not in legal:
            return False
        undo_info = apply_move(self._board, self._game_state, move)
        self._undo_stack.append((move, undo_info))
        self._redo_stack.clear()
        self._last_move = move
        self._selected_square = None
        return True

    def make_move_to_square(self, to_square: tuple[int, int], promotion_piece: Optional[str] = None) -> bool:
        if self._selected_square is None:
            return False
        legal = self.get_legal_moves(self._selected_square)
        for m in legal:
            if m.to_square != to_square:
                continue
            if m.promotion_piece is not None:
                if promotion_piece is None or promotion_piece.upper() not in ("Q", "R", "B", "N"):
                    return False
                if m.promotion_piece != promotion_piece.upper():
                    continue
            return self.make_move(m)
        return False

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        move, undo_info = self._undo_stack.pop()
        undo_move(self._board, self._game_state, move, undo_info)
        self._redo_stack.append((move, undo_info))
        self._last_move = self._undo_stack[-1][0] if self._undo_stack else None
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        move, undo_info = self._redo_stack.pop()
        apply_move(self._board, self._game_state, move)
        self._undo_stack.append((move, undo_info))
        self._last_move = move
        return True

    def new_game(self) -> None:
        self.reset_to_fen(STARTING_FEN)
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._last_move = None
        self._selected_square = None

    def reset_to_fen(self, fen: str) -> None:
        self._board = Board()
        self._game_state = GameState.from_fen(fen, self._board)
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._last_move = None
        self._selected_square = None

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def get_clock_state(self) -> dict:
        return {}

    def set_clock_state(self, state: dict) -> None:
        pass
