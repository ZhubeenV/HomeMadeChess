def take_piece(piece, loc):
    if loc == piece.location:
        piece.dead

class Piece:
    def __init__(self, type, location):
        self.ty = type
        self.loc = location
        self.dead = False

class Pawn(Piece):
    location = [x,y]
    first_move = False


