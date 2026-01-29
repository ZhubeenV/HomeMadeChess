"""
2D chess board widget: drawing, HiDPI-aware scaling, click handling.
Renders: normal squares, selected piece, legal moves, captures, last move, check.
"""

from typing import Optional

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsItem

from core.piece import WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING

PIECE_SYMBOLS = {
    (WHITE, PAWN): "\u2659", (WHITE, KNIGHT): "\u2658", (WHITE, BISHOP): "\u2657",
    (WHITE, ROOK): "\u2656", (WHITE, QUEEN): "\u2655", (WHITE, KING): "\u2654",
    (BLACK, PAWN): "\u265f", (BLACK, KNIGHT): "\u265e", (BLACK, BISHOP): "\u265d",
    (BLACK, ROOK): "\u265c", (BLACK, QUEEN): "\u265b", (BLACK, KING): "\u265a",
}

LIGHT_SQUARE = QColor(240, 217, 181)
DARK_SQUARE = QColor(181, 136, 99)
SELECTED_SQUARE = QColor(246, 246, 105)
LAST_MOVE = QColor(205, 210, 106)
LEGAL_MOVE = QColor(120, 120, 120, 80)
LEGAL_CAPTURE = QColor(180, 80, 80, 120)
CHECK_SQUARE = QColor(200, 80, 80)


class ChessSquareItem(QGraphicsRectItem):
    def __init__(self, rank: int, file: int, size: float, parent=None):
        super().__init__(0, 0, size, size, parent)
        self.rank = rank
        self.file = file
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

    def square(self) -> tuple[int, int]:
        return (self.rank, self.file)


class BoardWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setMinimumSize(320, 320)
        self.setStyleSheet("background: #2b2b2b;")
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._square_size = 60.0
        self._squares: list[list[ChessSquareItem]] = []
        self._piece_items: dict[tuple[int, int], QGraphicsItem] = {}
        self._legal_move_items: list[QGraphicsItem] = []
        self._controller = None
        self._promotion_callback = None
        self._legal_moves: set[tuple[int, int]] = set()
        self._selected_square: Optional[tuple[int, int]] = None
        self._last_move: Optional[tuple[tuple[int, int], tuple[int, int]]] = None
        self._check_square: Optional[tuple[int, int]] = None
        self._build_board()

    def set_controller(self, controller) -> None:
        self._controller = controller

    def set_promotion_callback(self, callback) -> None:
        self._promotion_callback = callback

    def _build_board(self) -> None:
        self._scene.clear()
        self._squares = []
        self._piece_items.clear()
        self._legal_move_items = []
        for rank in range(8):
            row = []
            for file in range(8):
                is_light = (rank + file) % 2 == 0
                color = LIGHT_SQUARE if is_light else DARK_SQUARE
                item = ChessSquareItem(rank, file, self._square_size)
                item.setBrush(QBrush(color))
                item.setPen(QPen(Qt.PenStyle.NoPen))
                item.setPos(file * self._square_size, (7 - rank) * self._square_size)
                self._scene.addItem(item)
                row.append(item)
            self._squares.append(row)
        self.setSceneRect(0, 0, 8 * self._square_size, 8 * self._square_size)

    def _update_square_colors(self) -> None:
        for rank in range(8):
            for file in range(8):
                sq = self._squares[rank][file]
                is_light = (rank + file) % 2 == 0
                base = LIGHT_SQUARE if is_light else DARK_SQUARE
                if (rank, file) == self._check_square:
                    sq.setBrush(QBrush(CHECK_SQUARE))
                elif (rank, file) == self._selected_square:
                    sq.setBrush(QBrush(SELECTED_SQUARE))
                elif self._last_move and ((rank, file) == self._last_move[0] or (rank, file) == self._last_move[1]):
                    sq.setBrush(QBrush(LAST_MOVE))
                else:
                    sq.setBrush(QBrush(base))
        self._draw_legal_move_indicators()
        self._draw_pieces()

    def _draw_legal_move_indicators(self) -> None:
        for item in self._legal_move_items:
            self._scene.removeItem(item)
        self._legal_move_items.clear()
        sz = self._square_size
        dot_sz = sz * 0.25
        for (rank, file) in self._legal_moves:
            if self._controller is None:
                continue
            piece = self._controller.get_board().get_piece_at(rank, file)
            x = file * sz + (sz - dot_sz) / 2
            y = (7 - rank) * sz + (sz - dot_sz) / 2
            if piece is not None:
                ell = self._scene.addEllipse(x, y, dot_sz, dot_sz, QPen(Qt.PenStyle.NoPen), QBrush(LEGAL_CAPTURE))
            else:
                ell = self._scene.addEllipse(x + (dot_sz - sz * 0.15) / 2, y + (dot_sz - sz * 0.15) / 2, sz * 0.15, sz * 0.15, QPen(Qt.PenStyle.NoPen), QBrush(LEGAL_MOVE))
            ell.setZValue(1)
            self._legal_move_items.append(ell)

    def _draw_pieces(self) -> None:
        for item in self._piece_items.values():
            self._scene.removeItem(item)
        self._piece_items.clear()
        if self._controller is None:
            return
        board = self._controller.get_board()
        font = QFont("Segoe UI Symbol", int(self._square_size * 0.7))
        for rank in range(8):
            for file in range(8):
                piece = board.get_piece_at(rank, file)
                if piece is not None:
                    sym = PIECE_SYMBOLS.get((piece.color, piece.piece_type), "?")
                    text = self._scene.addSimpleText(sym)
                    text.setFont(font)
                    text.setBrush(QBrush(QColor(255, 255, 255)) if piece.color == WHITE else QBrush(QColor(30, 30, 30)))
                    text.setPos(file * self._square_size + self._square_size * 0.15, (7 - rank) * self._square_size + self._square_size * 0.05)
                    self._piece_items[(rank, file)] = text
        for item in self._piece_items.values():
            item.setZValue(2)

    def _refresh_state(self) -> None:
        if self._controller is None:
            return
        self._selected_square = self._controller.get_selected_square()
        self._last_move = None
        last = self._controller.get_last_move()
        if last is not None:
            self._last_move = (last.from_square, last.to_square)
        self._legal_moves = set()
        if self._selected_square is not None:
            for m in self._controller.get_legal_moves(self._selected_square):
                self._legal_moves.add(m.to_square)
        status = self._controller.get_status()
        self._check_square = None
        if status in ("check", "checkmate"):
            board = self._controller.get_board()
            state = self._controller.get_game_state()
            side = state.side_to_move
            for r in range(8):
                for f in range(8):
                    p = board.get_piece_at(r, f)
                    if p is not None and p.piece_type == KING and p.color == side:
                        self._check_square = (r, f)
                        break
        self._update_square_colors()

    def refresh(self) -> None:
        self._refresh_state()
        self.viewport().update()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w = self.viewport().width()
        h = self.viewport().height()
        cell = min(w, h) / 8
        self._square_size = cell
        self._build_board()
        self._refresh_state()

    def _scene_pos_to_square(self, pos: QPointF) -> Optional[tuple[int, int]]:
        file = int(pos.x() / self._square_size)
        rank = 7 - int(pos.y() / self._square_size)
        if 0 <= rank < 8 and 0 <= file < 8:
            return (rank, file)
        return None

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.position().toPoint())
            square = self._scene_pos_to_square(pos)
            if square is not None and self._controller is not None:
                self.square_clicked(square)
        super().mousePressEvent(event)

    def square_clicked(self, square: tuple[int, int]) -> None:
        if self._controller is None:
            return
        board = self._controller.get_board()
        state = self._controller.get_game_state()
        piece = board.get_piece_at(square[0], square[1])
        selected = self._controller.get_selected_square()
        if selected is not None:
            if square == selected:
                self._controller.clear_selection()
            elif square in {m.to_square for m in self._controller.get_legal_moves(selected)}:
                moves = [m for m in self._controller.get_legal_moves(selected) if m.to_square == square]
                if len(moves) == 1 and moves[0].promotion_piece is None:
                    self._controller.make_move(moves[0])
                elif len(moves) > 1 and all(m.promotion_piece for m in moves):
                    if self._promotion_callback:
                        chosen = self._promotion_callback(moves)
                        if chosen is not None:
                            self._controller.make_move(chosen)
                    else:
                        self._controller.make_move(moves[0])
                else:
                    self._controller.make_move(moves[0])
            else:
                self._controller.select(square) if piece is not None and piece.color == state.side_to_move else self._controller.clear_selection()
        else:
            if piece is not None and piece.color == state.side_to_move:
                self._controller.select(square)
            else:
                self._controller.clear_selection()
        self.refresh()
