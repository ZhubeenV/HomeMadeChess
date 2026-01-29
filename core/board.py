"""
8x8 chess board: piece placement and square queries.

Coordinates: (rank, file), rank 0 = white's back rank (a1-h1), file 0 = a-file.
Board is stored as list of 8 lists (ranks), each of 8 Optional[Piece].
"""

from typing import Optional

from .piece import Piece, KING


class Board:
    """8x8 grid holding Piece references. Empty squares are None."""

    RANKS = 8
    FILES = 8

    def __init__(self) -> None:
        # board[rank][file] = Piece or None
        self._grid: list[list[Optional[Piece]]] = [
            [None] * self.FILES for _ in range(self.RANKS)
        ]

    def __getitem__(self, key: tuple[int, int]) -> Optional[Piece]:
        rank, file = key
        if not (0 <= rank < self.RANKS and 0 <= file < self.FILES):
            raise IndexError(f"square ({rank}, {file}) out of bounds")
        return self._grid[rank][file]

    def __setitem__(self, key: tuple[int, int], value: Optional[Piece]) -> None:
        rank, file = key
        if not (0 <= rank < self.RANKS and 0 <= file < self.FILES):
            raise IndexError(f"square ({rank}, {file}) out of bounds")
        self._grid[rank][file] = value
        if value is not None:
            value.position = (rank, file)

    def is_valid_square(self, rank: int, file: int) -> bool:
        return 0 <= rank < self.RANKS and 0 <= file < self.FILES

    def get_piece_at(self, rank: int, file: int) -> Optional[Piece]:
        if not self.is_valid_square(rank, file):
            return None
        return self._grid[rank][file]

    def set_piece_at(self, rank: int, file: int, piece: Optional[Piece]) -> None:
        if not self.is_valid_square(rank, file):
            raise IndexError(f"square ({rank}, {file}) out of bounds")
        self._grid[rank][file] = piece
        if piece is not None:
            piece.position = (rank, file)

    def clear_square(self, rank: int, file: int) -> None:
        self.set_piece_at(rank, file, None)

    def find_king(self, color: str) -> Optional[tuple[int, int]]:
        """Return (rank, file) of the king of the given color, or None."""
        from .piece import KING
        for r in range(self.RANKS):
            for f in range(self.FILES):
                p = self._grid[r][f]
                if p is not None and p.color == color and p.piece_type == KING:
                    return (r, f)
        return None

    def copy(self) -> "Board":
        """Return a shallow copy (same piece references). Use deep_copy for move simulation."""
        other = Board()
        for r in range(self.RANKS):
            for f in range(self.FILES):
                other._grid[r][f] = self._grid[r][f]
        return other

    def deep_copy(self) -> "Board":
        """Return a deep copy with new piece instances. Used for legal move filtering."""
        from .piece import piece_from_fen, WHITE
        other = Board()
        for r in range(self.RANKS):
            for f in range(self.FILES):
                p = self._grid[r][f]
                if p is not None:
                    sym = p.piece_type if p.color == WHITE else p.piece_type.lower()
                    other._grid[r][f] = piece_from_fen(sym, (r, f))
        return other
