import random
from typing import Optional
from src.schnapsen.game import Bot, PlayerPerspective, Move


class RandBot(Bot):
    def __init__(self, rand: random.Random) -> None:
        self.rng = rand

    def get_move(
        self,
        state: PlayerPerspective,
        leader_move: Optional[Move],
    ) -> Move:
        moves: list[Move] = state.valid_moves()
        move = self.rng.choice(list(moves))
        return move

    def __repr__(self) -> str:
        return f"RandBot: "
