"""
Game state: side to move, castling rights, en passant, halfmove/fullmove.
FEN parse and serialize. Board holds piece placement; GameState holds the rest.
"""

from typing import Optional

from .board import Board
from .piece import piece_from_fen, WHITE, BLACK

# Castling: K = white king-side, Q = white queen-side, k = black king-side, q = black queen-side
CASTLING_KEYS = "KQkq"

STARTING_FEN = (
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
)


class GameState:
    """
    Holds turn, castling rights, en passant target, halfmove clock, fullmove number.
    Does not hold piece placement (that is on Board).
    """

    def __init__(
        self,
        side_to_move: str = WHITE,
        castling_rights: str = CASTLING_KEYS,
        en_passant_target: Optional[tuple[int, int]] = None,
        halfmove_clock: int = 0,
        fullmove_number: int = 1,
    ) -> None:
        self.side_to_move = side_to_move
        self.castling_rights = castling_rights
        self.en_passant_target = en_passant_target  # (rank, file) or None
        self.halfmove_clock = halfmove_clock
        self.fullmove_number = fullmove_number

    def copy(self) -> "GameState":
        return GameState(
            side_to_move=self.side_to_move,
            castling_rights=self.castling_rights,
            en_passant_target=self.en_passant_target,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
        )

    @staticmethod
    def fen_square_to_coords(sq: str) -> tuple[int, int]:
        """Convert FEN square (e.g. e4) to (rank, file). a1=(0,0), h8=(7,7)."""
        if len(sq) != 2:
            raise ValueError(f"invalid FEN square: {sq}")
        file_char, rank_char = sq[0].lower(), sq[1]
        file_idx = ord(file_char) - ord("a")
        rank_idx = 8 - int(rank_char)
        if not (0 <= file_idx < 8 and 0 <= rank_idx < 8):
            raise ValueError(f"invalid FEN square: {sq}")
        return (rank_idx, file_idx)

    @staticmethod
    def coords_to_fen_square(rank: int, file: int) -> str:
        """Convert (rank, file) to FEN square (e.g. e4)."""
        return f"{chr(ord('a') + file)}{8 - rank}"

    @classmethod
    def from_fen(cls, fen: str, board: Board) -> "GameState":
        """
        Parse FEN into board placement and return a GameState for the rest.
        Mutates board. FEN format: "pieces w KQkq e3 0 1" (6 fields).
        """
        parts = fen.split()
        if len(parts) < 4:
            raise ValueError("FEN must have at least 4 fields")

        # Piece placement (first field). FEN rank 8 is first row, rank 1 is last row.
        # We use rank 0 = white's back rank (a1-h1), so our_rank = 7 - fen_rank_index.
        placement = parts[0]
        rank_strs = placement.split("/")
        if len(rank_strs) != 8:
            raise ValueError("FEN placement must have 8 ranks")
        for rank_idx, rank_str in enumerate(rank_strs):
            our_rank = 7 - rank_idx
            file_idx = 0
            for c in rank_str:
                if c.isdigit():
                    n = int(c)
                    for _ in range(n):
                        board.set_piece_at(our_rank, file_idx, None)
                        file_idx += 1
                else:
                    pos = (our_rank, file_idx)
                    piece = piece_from_fen(c, pos)
                    board.set_piece_at(our_rank, file_idx, piece)
                    file_idx += 1
            if file_idx != 8:
                raise ValueError(f"rank {rank_idx} has {file_idx} files")

        # Side to move
        side = parts[1].lower()
        if side == "w":
            side_to_move = WHITE
        elif side == "b":
            side_to_move = BLACK
        else:
            raise ValueError("FEN side to move must be w or b")

        # Castling
        castling = parts[2]
        if castling != "-":
            castling = "".join(c for c in castling if c in CASTLING_KEYS)

        # En passant
        ep = parts[3]
        en_passant_target: Optional[tuple[int, int]] = None
        if ep != "-":
            en_passant_target = cls.fen_square_to_coords(ep)

        halfmove_clock = int(parts[4]) if len(parts) > 4 else 0
        fullmove_number = int(parts[5]) if len(parts) > 5 else 1

        return cls(
            side_to_move=side_to_move,
            castling_rights=castling,
            en_passant_target=en_passant_target,
            halfmove_clock=halfmove_clock,
            fullmove_number=fullmove_number,
        )

    def to_fen_placement(self, board: Board) -> str:
        """Produce only the piece placement part of FEN. FEN rank 8 first (our rank 7)."""
        rows = []
        for rank in range(7, -1, -1):
            s = ""
            empty = 0
            for file in range(8):
                p = board.get_piece_at(rank, file)
                if p is None:
                    empty += 1
                else:
                    if empty:
                        s += str(empty)
                        empty = 0
                    sym = p.piece_type if p.color == WHITE else p.piece_type.lower()
                    s += sym
            if empty:
                s += str(empty)
            rows.append(s)
        return "/".join(rows)

    def to_fen(self, board: Board) -> str:
        """Full FEN string from current board and this state."""
        placement = self.to_fen_placement(board)
        side = "w" if self.side_to_move == WHITE else "b"
        castling = self.castling_rights if self.castling_rights else "-"
        ep = "-"
        if self.en_passant_target is not None:
            ep = self.coords_to_fen_square(*self.en_passant_target)
        return f"{placement} {side} {castling} {ep} {self.halfmove_clock} {self.fullmove_number}"
