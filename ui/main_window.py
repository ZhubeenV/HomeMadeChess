"""
Main application window: board, menu (New game, Undo, Redo), status line.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QMenuBar,
    QDialog, QHBoxLayout, QPushButton,
)
from PySide6.QtGui import QAction
from typing import TYPE_CHECKING

from .board_widget import BoardWidget
if TYPE_CHECKING:
    from core.move import Move


class PromotionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Promote pawn")
        self._choice = "Q"
        layout = QHBoxLayout(self)
        for sym, label in [("Q", "Queen"), ("R", "Rook"), ("B", "Bishop"), ("N", "Knight")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked=False, s=sym: self._set_choice(s))
            layout.addWidget(btn)
        self.setLayout(layout)

    def _set_choice(self, sym: str) -> None:
        self._choice = sym
        self.accept()

    def choice(self) -> str:
        return self._choice


class MainWindow(QMainWindow):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self.setWindowTitle("Chess")
        self.setMinimumSize(400, 450)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        self._board = BoardWidget(self)
        self._board.set_controller(controller)
        self._board.set_promotion_callback(self._promotion_choice)
        layout.addWidget(self._board)
        self._status_label = QLabel("White to move")
        self._status_label.setStyleSheet("font-size: 14px; padding: 8px;")
        layout.addWidget(self._status_label)
        self._build_menu()
        self._update_status()

    def _build_menu(self) -> None:
        menubar = self.menuBar()
        game_menu = menubar.addMenu("Game")
        new_action = QAction("New game", self)
        new_action.triggered.connect(self._new_game)
        game_menu.addAction(new_action)
        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self._undo)
        game_menu.addAction(undo_action)
        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self._redo)
        game_menu.addAction(redo_action)

    def _new_game(self) -> None:
        self._controller.new_game()
        self._update_status()
        self._board.refresh()

    def _undo(self) -> None:
        if self._controller.can_undo():
            self._controller.undo()
            self._update_status()
            self._board.refresh()

    def _redo(self) -> None:
        if self._controller.can_redo():
            self._controller.redo()
            self._update_status()
            self._board.refresh()

    def _promotion_choice(self, moves) -> "Move | None":
        dlg = PromotionDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            sym = dlg.choice()
            for m in moves:
                if m.promotion_piece == sym:
                    return m
        return None

    def _update_status(self) -> None:
        status = self._controller.get_status()
        state = self._controller.get_game_state()
        side = "White" if state.side_to_move == "white" else "Black"
        if status == "playing":
            self._status_label.setText(f"{side} to move")
        elif status == "check":
            self._status_label.setText(f"{side} to move — Check")
        elif status == "checkmate":
            winner = "Black" if state.side_to_move == "white" else "White"
            self._status_label.setText(f"Checkmate — {winner} wins")
        elif status == "stalemate":
            self._status_label.setText("Stalemate — Draw")
        else:
            self._status_label.setText(f"{side} to move")
        self._status_label.repaint()
