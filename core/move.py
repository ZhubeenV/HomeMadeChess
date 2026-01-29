"""
Move representation for chess.

Coordinates use (rank, file): rank 0 = white's back rank (a1-h1), file 0 = a-file.
So a1 = (0, 0), h1 = (0, 7), a8 = (7, 0), h8 = (7, 7).
"""

from dataclasses import dataclass
from typing import Optional


# Piece type symbols for promotion (Q, R, B, N)
PROMOTION_PIECES = ("Q", "R", "B", "N")


@dataclass(frozen=True)
class Move:
    """
    Immutable value object for a single move.
    Used for undo stack, FEN updates, and legal move lists.
    """

    from_square: tuple[int, int]  # (rank, file)
    to_square: tuple[int, int]
    promotion_piece: Optional[str] = None  # "Q", "R", "B", "N" or None
    is_castle: bool = False
    is_en_passant: bool = False
    is_double_pawn_push: bool = False

    def __post_init__(self) -> None:
        if self.promotion_piece is not None and self.promotion_piece not in PROMOTION_PIECES:
            raise ValueError(f"promotion_piece must be one of {PROMOTION_PIECES}")

    def uci_style(self) -> str:
        """Return UCI-style move string (e.g. e2e4, e7e8q)."""
        r0, f0 = self.from_square
        r1, f1 = self.to_square
        files = "abcdefgh"
        from_str = f"{files[f0]}{8 - r0}"
        to_str = f"{files[f1]}{8 - r1}"
        promo = self.promotion_piece or ""
        return from_str + to_str + promo.lower()
