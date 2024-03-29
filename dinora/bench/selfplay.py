import pathlib
import time

import chess

from dinora.engine import Engine
from dinora.mcts import MoveTimeConstraint


def selfplay(model_name: str, weights: pathlib.Path, device: str) -> None:
    engine = Engine(model_name, weights, device)
    engine.mcts_params.send_func = lambda _: None
    engine.load_model()
    engine.get_best_move(chess.Board(), MoveTimeConstraint(100))  # Warmup
    print("Engine loaded")

    board = chess.Board()

    total_visits = 0
    total_moves = 0
    start_time = time.time()

    try:
        while not board.is_game_over(claim_draw=True):
            node = engine.get_best_node(board, MoveTimeConstraint(1000))
            assert node.move
            assert node.parent
            print(
                f"{total_moves}. Move {node.move.uci()}"
                f"\tnodes {node.parent.number_visits}"
            )

            total_moves += 1
            total_visits += node.parent.number_visits
            board.push(node.move)
    except KeyboardInterrupt:
        print("Bench canceled by keyboard interrupt")
    finally:
        elapsed_time = time.time() - start_time
        average_nps = total_visits / elapsed_time
        print(
            f"Average nps {average_nps:.2f}"
            f"\tTotal moves {total_moves}"
            f"\tElapsed_time {elapsed_time}"
        )
