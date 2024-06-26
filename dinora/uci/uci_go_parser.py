from dataclasses import dataclass

import chess

from dinora.search.stoppers import (
    Infinite,
    MoveTime,
    NodesCount,
    Stopper,
    Time,
)


@dataclass
class UciGoParams:
    wtime: int | None = None
    btime: int | None = None
    winc: int | None = None
    binc: int | None = None
    nodes: int | None = None
    movetime: int | None = None
    infinite: bool = False

    def is_time(self, turn: bool) -> tuple[int, int] | None:
        """
        Time for whole game or whole game with increment
        from parsed wtime, btime, winc, binc
        """
        # Can return time only if both wtime and btime specified
        if not (self.wtime and self.btime):
            return None
        engine_time = self.wtime if turn else self.btime
        engine_inc = (self.winc if turn else self.binc) or 0
        return engine_time, engine_inc

    def get_search_stopper(self, board: chess.Board) -> Stopper:
        stopper: Stopper
        if self.infinite:
            stopper = Infinite()

        elif isinstance(self.movetime, int):
            stopper = MoveTime(self.movetime)

        elif time := self.is_time(board.turn):
            engine_time, engine_inc = time
            stopper = Time(
                moves_number=board.fullmove_number,
                engine_time=engine_time,
                engine_inc=engine_inc,
            )

        elif nodes := self.nodes:
            stopper = NodesCount(nodes)

        else:
            stopper = Infinite()

        return stopper


def parse_go_params(tokens: list[str]) -> UciGoParams:
    params = UciGoParams()
    i = 0

    def end() -> bool:
        return i >= len(tokens)

    def consume_tok() -> str | None:
        nonlocal i
        if end():
            return None
        tok = tokens[i]
        i += 1
        return tok

    while not end():
        currtok = consume_tok()

        # tokens with integer value
        if currtok in [
            "wtime",
            "btime",
            "winc",
            "binc",
            "nodes",
            "movetime",
        ]:
            val = consume_tok()
            setattr(params, currtok, int(val))  # type: ignore

        if currtok == "infinite":
            params.infinite = True

    return params
