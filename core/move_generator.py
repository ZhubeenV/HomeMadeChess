"""
Legal move generation: pseudo-legal moves per piece, then filter by "no self-check".
King cannot castle out of, through, or into check. Pins and check constraints
are enforced by filtering: only moves that leave our king unattackable are legal.
"""

from typing import Optional

from .board import Board
from .game_state import GameState
from .move import Move, PROMOTION_PIECES
from .piece import (
    Piece, Pawn, Knight, Bishop, Rook, Queen, King,
    WHITE, BLACK, PAWN, KNIGHT, ROOK, KING,
)
from .apply import apply_move


def square_attacked_by(
    board: Board,
    square: tuple[int, int],
    by_color: str,
    exclude_square: Optional[tuple[int, int]] = None,
) -> bool:
    """
    Return True if the given square is attacked by any piece of by_color.
    exclude_square: optional (rank, file) to treat as empty (for discovering checks through a piece).
    """
    rank, file = square
    # Pawns
    direction = 1 if by_color == WHITE else -1
    for df in (-1, 1):
        r2 = rank + direction
        f2 = file + df
        if board.is_valid_square(r2, f2):
            p = board.get_piece_at(r2, f2)
            if p is not None and p.color == by_color and p.piece_type == PAWN:
                return True

    # Knights
    for dr, df in Knight.move_deltas:
        r2, f2 = rank + dr, file + df
        if board.is_valid_square(r2, f2):
            p = board.get_piece_at(r2, f2)
            if p is not None and p.color == by_color and p.piece_type == KNIGHT:
                return True

    # Sliding: rook/queen (horizontal/vertical), bishop/queen (diagonal)
    rook_deltas = Rook.move_deltas
    bishop_deltas = Bishop.move_deltas
    for dr, df in rook_deltas + bishop_deltas:
        r2, f2 = rank + dr, file + df
        while board.is_valid_square(r2, f2):
            p = board.get_piece_at(r2, f2)
            if p is not None:
                if (r2, f2) == exclude_square:
                    r2 += dr
                    f2 += df
                    continue
                if p.color == by_color:
                    if p.piece_type in (ROOK, "Q") and (dr == 0 or df == 0):
                        return True
                    if p.piece_type in ("B", "Q") and dr != 0 and df != 0:
                        return True
                break
            r2 += dr
            f2 += df

    # King (one square)
    for dr, df in King.move_deltas:
        r2, f2 = rank + dr, file + df
        if board.is_valid_square(r2, f2):
            p = board.get_piece_at(r2, f2)
            if p is not None and p.color == by_color and p.piece_type == KING:
                return True

    return False


def _pseudo_legal_pawn_moves(
    board: Board,
    game_state: GameState,
    piece: Pawn,
) -> list[Move]:
    r0, f0 = piece.position
    dr = piece.direction
    moves = []
    # One forward
    r1 = r0 + dr
    if board.is_valid_square(r1, f0) and board.get_piece_at(r1, f0) is None:
        if r1 in (0, 7):  # Promotion
            for promo in PROMOTION_PIECES:
                moves.append(Move((r0, f0), (r1, f0), promotion_piece=promo))
        else:
            moves.append(Move((r0, f0), (r1, f0)))
            # Two forward from start
            if r0 == piece.start_rank:
                r2 = r0 + 2 * dr
                if board.get_piece_at(r2, f0) is None:
                    moves.append(Move((r0, f0), (r2, f0), is_double_pawn_push=True))
    # Captures
    for df in (-1, 1):
        r1, f1 = r0 + dr, f0 + df
        if board.is_valid_square(r1, f1):
            target = board.get_piece_at(r1, f1)
            if target is not None and target.color != piece.color:
                if r1 in (0, 7):
                    for promo in PROMOTION_PIECES:
                        moves.append(Move((r0, f0), (r1, f1), promotion_piece=promo))
                else:
                    moves.append(Move((r0, f0), (r1, f1)))
    # En passant
    ep = game_state.en_passant_target
    if ep is not None:
        ep_rank, ep_file = ep
        if r0 + dr == ep_rank and abs(f0 - ep_file) == 1:
            moves.append(Move((r0, f0), (ep_rank, ep_file), is_en_passant=True))
    return moves


def _pseudo_legal_sliding_moves(
    board: Board,
    piece: Piece,
    deltas: list[tuple[int, int]],
) -> list[Move]:
    r0, f0 = piece.position
    moves = []
    for dr, df in deltas:
        r, f = r0 + dr, f0 + df
        while board.is_valid_square(r, f):
            target = board.get_piece_at(r, f)
            if target is None:
                moves.append(Move((r0, f0), (r, f)))
            else:
                if target.color != piece.color:
                    moves.append(Move((r0, f0), (r, f)))
                break
            r += dr
            f += df
    return moves


def _pseudo_legal_knight_king_moves(
    board: Board,
    piece: Piece,
    deltas: list[tuple[int, int]],
) -> list[Move]:
    r0, f0 = piece.position
    moves = []
    for dr, df in deltas:
        r, f = r0 + dr, f0 + df
        if board.is_valid_square(r, f):
            target = board.get_piece_at(r, f)
            if target is None or target.color != piece.color:
                moves.append(Move((r0, f0), (r, f)))
    return moves


def _pseudo_legal_castling(
    board: Board,
    game_state: GameState,
    piece: King,
) -> list[Move]:
    r0, f0 = piece.position
    moves = []
    rights = game_state.castling_rights
    if piece.color == WHITE:
        if "K" in rights and board.get_piece_at(r0, 5) is None and board.get_piece_at(r0, 6) is None:
            if not square_attacked_by(board, (r0, f0), BLACK) and \
               not square_attacked_by(board, (r0, 5), BLACK) and \
               not square_attacked_by(board, (r0, 6), BLACK):
                moves.append(Move((r0, f0), (r0, 6), is_castle=True))
        if "Q" in rights and board.get_piece_at(r0, 1) is None and board.get_piece_at(r0, 2) is None and board.get_piece_at(r0, 3) is None:
            if not square_attacked_by(board, (r0, f0), BLACK) and \
               not square_attacked_by(board, (r0, 3), BLACK) and \
               not square_attacked_by(board, (r0, 2), BLACK):
                moves.append(Move((r0, f0), (r0, 2), is_castle=True))
    else:
        if "k" in rights and board.get_piece_at(r0, 5) is None and board.get_piece_at(r0, 6) is None:
            if not square_attacked_by(board, (r0, f0), WHITE) and \
               not square_attacked_by(board, (r0, 5), WHITE) and \
               not square_attacked_by(board, (r0, 6), WHITE):
                moves.append(Move((r0, f0), (r0, 6), is_castle=True))
        if "q" in rights and board.get_piece_at(r0, 1) is None and board.get_piece_at(r0, 2) is None and board.get_piece_at(r0, 3) is None:
            if not square_attacked_by(board, (r0, f0), WHITE) and \
               not square_attacked_by(board, (r0, 3), WHITE) and \
               not square_attacked_by(board, (r0, 2), WHITE):
                moves.append(Move((r0, f0), (r0, 2), is_castle=True))
    return moves


def _pseudo_legal_moves_for_piece(
    board: Board,
    game_state: GameState,
    piece: Piece,
) -> list[Move]:
    if piece.piece_type == PAWN:
        return _pseudo_legal_pawn_moves(board, game_state, piece)
    if piece.piece_type == KNIGHT:
        return _pseudo_legal_knight_king_moves(board, piece, Knight.move_deltas)
    if piece.piece_type == Bishop.piece_type:
        return _pseudo_legal_sliding_moves(board, piece, Bishop.move_deltas)
    if piece.piece_type == Rook.piece_type:
        return _pseudo_legal_sliding_moves(board, piece, Rook.move_deltas)
    if piece.piece_type == Queen.piece_type:
        return _pseudo_legal_sliding_moves(board, piece, Queen.move_deltas)
    if piece.piece_type == KING:
        moves = _pseudo_legal_knight_king_moves(board, piece, King.move_deltas)
        moves.extend(_pseudo_legal_castling(board, game_state, piece))
        return moves
    return []


def get_legal_moves(
    board: Board,
    game_state: GameState,
    from_square: Optional[tuple[int, int]] = None,
) -> list[Move]:
    """
    Return all legal moves for side_to_move. If from_square is given, return only
    moves from that square. Two-phase: pseudo-legal then filter by "king not in check after move".
    """
    side = game_state.side_to_move
    opponent = BLACK if side == WHITE else WHITE
    pseudo = []
    for r in range(8):
        for f in range(8):
            if from_square is not None and (r, f) != from_square:
                continue
            p = board.get_piece_at(r, f)
            if p is not None and p.color == side:
                pseudo.extend(_pseudo_legal_moves_for_piece(board, game_state, p))
    legal = []
    for move in pseudo:
        board_copy = board.deep_copy()
        state_copy = game_state.copy()
        apply_move(board_copy, state_copy, move)
        king_pos = board_copy.find_king(side)
        if king_pos is None:
            continue
        if not square_attacked_by(board_copy, king_pos, opponent):
            legal.append(move)
    return legal
