import chess
import numpy as np
from dinora.board_representation import canon_input_planes
from dinora.board_representation2 import board_to_tensor


def test_shape_and_type_old():
    tensor = canon_input_planes(chess.STARTING_FEN, False)
    assert tensor.shape == (18, 8, 8)
    assert tensor.dtype == np.float32


def test_shape_and_type_new():
    tensor = board_to_tensor(chess.Board())
    assert tensor.shape == (18, 8, 8)
    assert tensor.dtype == np.float32


def test_old_new_regression():
    FENS = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        "1r3rk1/p1R2ppp/4p3/3pP3/3P1PP1/q1N1Q3/n6P/5RK1 w - - 0 21",
        "8/5kp1/8/4P1PP/4K3/8/5r2/8 b - - 2 60",
        "r1b1r1k1/pp1n1p2/2p5/3p2p1/4PpPp/2PP1P1P/PP4B1/R3KN1R w KQ - 0 18",
        "rnbqkbnr/1pp1pppp/p7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3",  # White can en passant
        "rnbqkbnr/1pp1pp1p/p7/3pP3/6pP/3P4/PPP1BPP1/RNBQK1NR b KQkq h3 0 5",  # Black can en passant
    ]

    for fen in FENS:
        tensor_old = canon_input_planes(fen, not chess.Board(fen).turn)
        tensor_new = board_to_tensor(chess.Board(fen))

        # [1: 12) layers are now flipped in new board representation
        for i in range(12):
            tensor_new[i] = np.flip(tensor_new[i], 0)

        if chess.Board(fen).turn:  # there is the bug with board flip in old repr
            tensor_new[17] = np.flip(tensor_new[17], 0)

        assert np.allclose(tensor_old, tensor_new)