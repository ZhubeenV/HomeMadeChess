"""Tests for legal move generation."""

import pytest
from core.board import Board
from core.game_state import GameState, STARTING_FEN
from core.move_generator import get_legal_moves
from core.move import Move


def test_start_position_white_has_20_moves() -> None:
    board = Board()
    state = GameState.from_fen(STARTING_FEN, board)
    moves = get_legal_moves(board, state)
    assert len(moves) == 20


def test_white_pawn_double_push_from_start() -> None:
    board = Board()
    state = GameState.from_fen(STARTING_FEN, board)
    moves = get_legal_moves(board, state, (1, 4))  # e2
    assert any(m.from_square == (1, 4) and m.to_square == (3, 4) and m.is_double_pawn_push for m in moves)


def test_king_cannot_move_into_check() -> None:
    # Position: white king on e1, black king on e8 - king can move
    fen = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
    board = Board()
    state = GameState.from_fen(fen, board)
    moves = get_legal_moves(board, state, (0, 4))
    assert len(moves) >= 1  # King can move
    # Queen on e5 attacking e2: king cannot move to e2 (would be in check)
    fen2 = "4k3/8/8/4q3/8/8/8/4K3 w - - 0 1"
    board2 = Board()
    state2 = GameState.from_fen(fen2, board2)
    moves2 = get_legal_moves(board2, state2, (0, 4))
    to_squares = {m.to_square for m in moves2}
    assert (1, 4) not in to_squares  # e2 is attacked by queen on e5
