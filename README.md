# HomeMadeChess

A modular, rule-complete chess application in Python with a desktop UI (PySide6). Game logic is separate from the UI so a web frontend could be swapped in later.

## Run locally

```bash
cd lpg
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Run from the project root (`lpg`) so that the `core` and `game` packages resolve.

Run tests:

```bash
python3 -m pytest tests/ -v
```

## Move validation and game state

**Move validation**  
Legal moves are produced in two steps:

1. **Pseudo-legal moves**: For each piece of the side to move, generate moves that obey that piece’s rules (sliding, knight L, pawn push/capture/en passant, king one-square and castling). Castling uses game state (rights, empty path, king/through squares not attacked). En passant uses the current FEN en passant target. Pawn promotion adds four moves (Q, R, B, N) per promotion square.

2. **Filter for self-check**: For each pseudo-legal move, apply it on a deep copy of the board and game state, then test whether the moving side’s king is attacked. Only moves that leave the king safe are returned as legal. So illegal self-check is avoided by construction.

**Game state**  
- **Board**: 8×8 grid of pieces; coordinates `(rank, file)` with rank 0 = white’s back rank, file 0 = a-file.  
- **GameState**: Side to move, castling rights (KQkq), en passant target square, halfmove clock, fullmove number.  
- **FEN**: Used to load the start position and to serialize the position. Board holds piece placement; GameState holds the rest. Parsing and export are in `core/game_state.py`.

**Undo/redo**  
The controller keeps an undo stack of `(Move, UndoInfo)`. UndoInfo stores captured piece and square, rook from/to for castling, and previous castling/en passant/halfmove. Undo reapplies that data to restore the previous position.

## Optional: engine integration

The base game runs without any external engine. A future “hint” or “analysis” feature could call an engine (e.g. Stockfish) behind a small interface (e.g. `get_best_move(fen)`) without changing core move generation or validation.
