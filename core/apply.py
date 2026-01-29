"""
Apply a move to board and game state. Used by GameController and by move_generator
for legality checks (apply on copy, then test for check).
Returns undo info for the controller's undo stack.
"""

from typing import Any, Optional

from .board import Board
from .game_state import GameState
from .move import Move
from .piece import (
    Piece, Pawn, Knight, Bishop, Rook, Queen, King,
    piece_from_fen, WHITE, BLACK, KING, ROOK, PAWN,
)

# Undo info: (captured_piece, captured_square, rook_from, rook_to, prev_castling, prev_ep, prev_halfmove)
UndoInfo = tuple[
    Optional[Piece], tuple[int, int],
    Optional[tuple[int, int]], Optional[tuple[int, int]],
    str, Optional[tuple[int, int]], int,
]


def apply_move(
    board: Board,
    game_state: GameState,
    move: Move,
) -> UndoInfo:
    """
    Apply move to board and game_state in place.
    Returns undo info: (captured_piece, captured_square, rook_from, rook_to,
                        prev_castling, prev_ep, prev_halfmove).
    """
    r0, f0 = move.from_square
    r1, f1 = move.to_square
    piece = board[r0, f0]
    if piece is None:
        raise ValueError("no piece at from_square")

    prev_castling = game_state.castling_rights
    prev_ep = game_state.en_passant_target
    prev_halfmove = game_state.halfmove_clock

    captured_piece: Optional[Piece] = None
    captured_square: tuple[int, int] = (r1, f1)
    rook_from: Optional[tuple[int, int]] = None
    rook_to: Optional[tuple[int, int]] = None

    # En passant: capture the pawn that was passed
    if move.is_en_passant:
        # Captured pawn is on same file as to_square, rank = from_square rank
        cap_rank, cap_file = r0, f1
        captured_piece = board[cap_rank, cap_file]
        board.clear_square(cap_rank, cap_file)
        captured_square = (cap_rank, cap_file)

    # Castling: move rook
    if move.is_castle:
        if f1 > f0:  # King-side
            rook_from = (r0, 7)
            rook_to = (r0, 5)
        else:  # Queen-side
            rook_from = (r0, 0)
            rook_to = (r0, 3)
        rook_piece = board[rook_from[0], rook_from[1]]
        board.clear_square(rook_from[0], rook_from[1])
        board.set_piece_at(rook_to[0], rook_to[1], rook_piece)

    # Capture (normal or already handled en passant)
    if not move.is_en_passant and board[r1, f1] is not None:
        captured_piece = board[r1, f1]
        board.clear_square(r1, f1)

    # Move the piece
    board.clear_square(r0, f0)
    if move.promotion_piece:
        promo_color = piece.color
        new_piece = piece_from_fen(
            move.promotion_piece if promo_color == WHITE else move.promotion_piece.lower(),
            (r1, f1),
        )
        board.set_piece_at(r1, f1, new_piece)
    else:
        board.set_piece_at(r1, f1, piece)

    # Update game state
    game_state.side_to_move = BLACK if game_state.side_to_move == WHITE else WHITE
    game_state.en_passant_target = None
    if piece.piece_type == PAWN or captured_piece is not None:
        game_state.halfmove_clock = 0
    else:
        game_state.halfmove_clock += 1
    if game_state.side_to_move == WHITE:
        game_state.fullmove_number += 1

    # Castling rights: remove for moved king or moved rook
    new_rights = list(game_state.castling_rights)
    if piece.piece_type == KING:
        if piece.color == WHITE:
            if "K" in new_rights:
                new_rights.remove("K")
            if "Q" in new_rights:
                new_rights.remove("Q")
        else:
            if "k" in new_rights:
                new_rights.remove("k")
            if "q" in new_rights:
                new_rights.remove("q")
    if piece.piece_type == ROOK:
        if piece.color == WHITE:
            if f0 == 7 and "K" in new_rights:
                new_rights.remove("K")
            if f0 == 0 and "Q" in new_rights:
                new_rights.remove("Q")
        else:
            if f0 == 7 and "k" in new_rights:
                new_rights.remove("k")
            if f0 == 0 and "q" in new_rights:
                new_rights.remove("q")
    # Remove castling right when a rook is captured
    if captured_piece is not None and captured_piece.piece_type == ROOK:
        if captured_square[1] == 7:
            if captured_piece.color == WHITE and "K" in new_rights:
                new_rights.remove("K")
            elif captured_piece.color == BLACK and "k" in new_rights:
                new_rights.remove("k")
        if captured_square[1] == 0:
            if captured_piece.color == WHITE and "Q" in new_rights:
                new_rights.remove("Q")
            elif captured_piece.color == BLACK and "q" in new_rights:
                new_rights.remove("q")
    game_state.castling_rights = "".join(new_rights) if new_rights else ""

    # En passant target: set after double pawn push
    if move.is_double_pawn_push:
        ep_rank = (r0 + r1) // 2
        game_state.en_passant_target = (ep_rank, f1)

    return (
        captured_piece,
        captured_square,
        rook_from,
        rook_to,
        prev_castling,
        prev_ep,
        prev_halfmove,
    )


def undo_move(
    board: Board,
    game_state: GameState,
    move: Move,
    undo_info: UndoInfo,
) -> None:
    """Reverse a move using undo_info from apply_move."""
    captured_piece, captured_square, rook_from, rook_to, prev_castling, prev_ep, prev_halfmove = undo_info
    r0, f0 = move.from_square
    r1, f1 = move.to_square
    piece = board[r1, f1]
    if piece is None:
        raise ValueError("no piece at to_square")

    # Flip turn back
    game_state.side_to_move = BLACK if game_state.side_to_move == WHITE else WHITE
    game_state.castling_rights = prev_castling
    game_state.en_passant_target = prev_ep
    game_state.halfmove_clock = prev_halfmove
    if game_state.side_to_move == BLACK:
        game_state.fullmove_number -= 1

    # Remove piece from destination
    board.clear_square(r1, f1)
    # Restore piece at source (if promotion, we need to put pawn back)
    from .piece import PAWN, Queen, Rook, Bishop, Knight
    if move.promotion_piece:
        promo_color = piece.color
        pawn = Pawn(promo_color, (r0, f0))
        board.set_piece_at(r0, f0, pawn)
    else:
        board.set_piece_at(r0, f0, piece)

    # Restore captured piece
    if captured_piece is not None:
        board.set_piece_at(captured_square[0], captured_square[1], captured_piece)

    # Undo castling: move rook back
    if move.is_castle and rook_from is not None and rook_to is not None:
        rook_piece = board[rook_to[0], rook_to[1]]
        board.clear_square(rook_to[0], rook_to[1])
        board.set_piece_at(rook_from[0], rook_from[1], rook_piece)
