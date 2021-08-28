import numpy as np
import math
import chess
from collections import OrderedDict
from time import time

FPU = -1.0
FPU_ROOT = 0.0


def cp(Q):
    return int(295 * Q / (1 - 0.976953125 * Q ** 14))


class UCTNode:
    def __init__(self, board=None, parent=None, move=None, prior=0):
        self.board = board
        self.move = move
        self.is_expanded = False
        self.parent = parent  # Optional[UCTNode]
        self.children = OrderedDict()  # Dict[move, UCTNode]
        self.prior = prior  # float
        if parent == None:
            self.total_value = FPU_ROOT  # float
        else:
            self.total_value = FPU
        self.number_visits = 0  # int

    def Q(self):  # returns float
        return self.total_value / (1 + self.number_visits)

    def U(self):  # returns float
        return (
            math.sqrt(self.parent.number_visits) * self.prior / (1 + self.number_visits)
        )

    def best_child(self, C):
        return max(self.children.values(), key=lambda node: node.Q() + C * node.U())

    def select_leaf(self, C):
        current = self
        while current.is_expanded and current.children:
            current = current.best_child(C)
        if not current.board:
            current.board = current.parent.board.copy()
            current.board.push_uci(current.move)
        return current

    def expand(self, child_priors):
        self.is_expanded = True
        for move, prior in child_priors.items():
            self.add_child(move, prior)

    def add_child(self, move, prior):
        self.children[move] = UCTNode(parent=self, move=move, prior=prior)

    def backup(self, value_estimate: float):
        current = self
        # Child nodes are multiplied by -1 because we want max(-opponent eval)
        turnfactor = -1
        while current.parent is not None:
            current.number_visits += 1
            current.total_value += value_estimate * turnfactor
            current = current.parent
            turnfactor *= -1
        current.number_visits += 1


def get_best_move(root):
    bestmove, node = max(
        root.children.items(), key=lambda item: (item[1].number_visits, item[1].Q())
    )
    score = int(round(cp(node.Q()), 0))
    return bestmove, node, score


def send_info(send, bestmove, count, delta, score):
    if send != None:
        send(
            "info depth 1 seldepth 1 score cp {} nodes {} nps {} pv {}".format(
                score, count, int(round(count / delta, 0)), bestmove
            )
        )


def send_tree_info(send, root):
    if send != None:
        for nd in sorted(root.children.items(), key=lambda item: item[1].number_visits):
            send(
                "info string {} {} \t(P: {}%) \t(Q: {})".format(
                    nd[1].move,
                    nd[1].number_visits,
                    round(nd[1].prior * 100, 2),
                    round(nd[1].Q(), 5),
                )
            )


def uct_nodes(board, nodes, net=None, C=1.0, send=None):
    start = time()
    count = 0
    delta_last = 0

    root = UCTNode(board)
    for _ in range(nodes):
        count += 1
        leaf = root.select_leaf(C)
        child_priors, value_estimate = net.evaluate(leaf.board)
        leaf.expand(child_priors)
        leaf.backup(value_estimate)
        now = time()
        delta = now - start
        if delta - delta_last > 5:  # Send info every 5 sec
            delta_last = delta
            bestmove, _, score = get_best_move(root)
            send_info(send, bestmove, count, delta, score)

    bestmove, _, score = get_best_move(root)
    
    send_tree_info(send, root)
    send_info(send, bestmove, count, delta, score)

    # if we have a bad score, go for a draw
    return bestmove, score


def uct_time(board, net, C, move_time, send):
    count = 0
    delta_last = 0

    root = UCTNode(board)
    start = time()

    for _ in range(2):  # Calculate min 2 nodes
        count += 1
        leaf = root.select_leaf(C)
        child_priors, value_estimate = net.evaluate(leaf.board)
        leaf.expand(child_priors)
        leaf.backup(value_estimate)

    while True:
        count += 1
        leaf = root.select_leaf(C)
        child_priors, value_estimate = net.evaluate(leaf.board)
        leaf.expand(child_priors)
        leaf.backup(value_estimate)

        now = time()
        delta = now - start
        if delta - delta_last > 5:
            delta_last = delta
            bestmove, _, score = get_best_move(root)
            send_info(send, bestmove, count, delta, score)

        if delta > move_time:
            break

    bestmove, _, score = get_best_move(root)

    send_tree_info(send, root)
    send_info(send, bestmove, count, delta, score)

    # if we have a bad score, go for a draw
    return bestmove, score


if __name__ == "__main__":
    from dinora.net import ChessModel, ChessModelWithCache

    fen = input("fen> ")
    nodes = int(input("nodes> "))
    c = float(input("c> "))

    board = chess.Board(fen)
    net = ChessModel()

    # from dinora.train import build_model, LightConfig, ModelConfig
    # net.net.model = build_model(LightConfig)

    uct_nodes(board, nodes, net, c, send=print)
