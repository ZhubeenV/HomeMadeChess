"""
Check, checkmate, stalemate. Uses attack logic from move_generator.
"""

from typing import Optional

from .board import Board
from .game_state import GameState
from .piece import WHITE
from .move_generator import get_legal_moves, square_attacked_by


def is_in_check(board: Board, game_state: GameState, color: Optional[str] = None) -> bool:
    """
    Return True if the king of the given color is in check.
    If color is None, use side_to_move from game_state.
    """
    from .piece import BLACK
    side = color if color is not None else game_state.side_to_move
    king_pos = board.find_king(side)
    if king_pos is None:
        return False
    opponent = BLACK if side == WHITE else WHITE
    return square_attacked_by(board, king_pos, opponent)


def get_game_status(
    board: Board,
    game_state: GameState,
) -> str:
    """
    Return one of: "playing", "check", "checkmate", "stalemate".
    "check" = side to move is in check but has moves.
    "checkmate" = side to move is in check and has no legal moves.
    "stalemate" = side to move is not in check and has no legal moves.
    """
    legal_moves = get_legal_moves(board, game_state)
    in_check = is_in_check(board, game_state)

    if not legal_moves:
        return "checkmate" if in_check else "stalemate"
    return "check" if in_check else "playing"
