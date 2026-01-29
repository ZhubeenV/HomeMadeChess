"""Tests for check, checkmate, stalemate."""

import pytest
from core.board import Board
from core.game_state import GameState
from core.rules import is_in_check, get_game_status
from core.move_generator import get_legal_moves


def test_start_position_not_in_check() -> None:
    board = Board()
    state = GameState.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", board)
    assert is_in_check(board, state, "white") is False
    assert is_in_check(board, state, "black") is False


def test_scholars_mate_position_black_in_check() -> None:
    fen = "r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4"
    board = Board()
    state = GameState.from_fen(fen, board)
    assert is_in_check(board, state, "black") is True
    assert get_game_status(board, state) == "checkmate"


def test_stalemate_example() -> None:
    fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    board = Board()
    state = GameState.from_fen(fen, board)
    moves = get_legal_moves(board, state)
    assert len(moves) == 0
    assert is_in_check(board, state, "black") is False
    assert get_game_status(board, state) == "stalemate"
