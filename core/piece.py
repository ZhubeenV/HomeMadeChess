"""
Chess piece types and base class.

Coordinates: (rank, file), rank 0 = white's back rank, file 0 = a-file.
Piece color is "white" or "black". Piece type is one of P, N, B, R, Q, K.
"""

from abc import ABC
from typing import ClassVar

# Piece type symbols (FEN / internal)
PAWN = "P"
KNIGHT = "N"
BISHOP = "B"
ROOK = "R"
QUEEN = "Q"
KING = "K"

WHITE = "white"
BLACK = "black"


class Piece(ABC):
    """Base class for all chess pieces. Subclasses define movement."""

    piece_type: ClassVar[str]
    move_deltas: ClassVar[list[tuple[int, int]]] = []

    def __init__(self, color: str, position: tuple[int, int]) -> None:
        if color not in (WHITE, BLACK):
            raise ValueError("color must be 'white' or 'black'")
        self.color = color
        self.position = position

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.color!r}, {self.position!r})"

    @property
    def is_white(self) -> bool:
        return self.color == WHITE


class Pawn(Piece):
    piece_type = PAWN
    move_deltas = []

    @property
    def start_rank(self) -> int:
        return 1 if self.is_white else 6

    @property
    def direction(self) -> int:
        return 1 if self.is_white else -1


class Knight(Piece):
    piece_type = KNIGHT
    move_deltas = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1),
    ]


class Bishop(Piece):
    piece_type = BISHOP
    move_deltas = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


class Rook(Piece):
    piece_type = ROOK
    move_deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Queen(Piece):
    piece_type = QUEEN
    move_deltas = [
        (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1),
    ]


class King(Piece):
    piece_type = KING
    move_deltas = [
        (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1),
    ]


def piece_from_fen(symbol: str, position: tuple[int, int]) -> Piece:
    """Create a Piece from a FEN character (e.g. P, n, K) and position."""
    symbol = symbol.strip()
    if not symbol:
        raise ValueError("empty piece symbol")
    color = WHITE if symbol.isupper() else BLACK
    t = symbol.upper()
    classes = {
        PAWN: Pawn, KNIGHT: Knight, BISHOP: Bishop,
        ROOK: Rook, QUEEN: Queen, KING: King,
    }
    if t not in classes:
        raise ValueError(f"unknown piece symbol: {symbol}")
    return classes[t](color, position)
