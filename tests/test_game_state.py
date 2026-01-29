"""Tests for FEN parse/serialize and GameState."""

import pytest
from core.board import Board
from core.game_state import GameState, STARTING_FEN


def test_starting_fen_roundtrip() -> None:
    board = Board()
    state = GameState.from_fen(STARTING_FEN, board)
    fen_out = state.to_fen(board)
    parts_in = STARTING_FEN.split()
    parts_out = fen_out.split()
    assert parts_out[0] == parts_in[0]
    assert parts_out[1] == parts_in[1]
    assert parts_out[2] == parts_in[2]
    assert parts_out[3] == parts_in[3]


def test_fen_placement_white_back_rank() -> None:
    board = Board()
    GameState.from_fen(STARTING_FEN, board)
    for f, sym in enumerate("RNBQKBNR"):
        p = board.get_piece_at(0, f)
        assert p is not None
        assert p.piece_type == sym
        assert p.color == "white"


def test_fen_placement_black_back_rank() -> None:
    board = Board()
    GameState.from_fen(STARTING_FEN, board)
    for f, sym in enumerate("rnbqkbnr"):
        p = board.get_piece_at(7, f)
        assert p is not None
        assert p.piece_type == sym.upper()
        assert p.color == "black"


def test_side_to_move() -> None:
    board = Board()
    state = GameState.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", board)
    assert state.side_to_move == "white"
    state2 = GameState.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1", board)
    assert state2.side_to_move == "black"
