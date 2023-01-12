import random
from typing import Optional
from src.schnapsen.game import Bot, PlayerPerspective, Move, SchnapsenTrickScorer

class BullyBot(Bot):
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(self.seed)
    def get_move(
        self,
        state: PlayerPerspective,
        leader_move: Optional[Move],
    ) -> Move:
        scorer = SchnapsenTrickScorer()
        moves = state.valid_moves()
        self.rng.shuffle(moves)
        moves_trump_suit = []
        moves_same_suit = []
        for move in list(moves):
            if move.is_trump_exchange():
                suit = move.cards[0].suit
            else:
                move = move.as_regular_move()
                suit = move.card.suit
            if suit == state.get_trump_suit():
                moves_trump_suit.append(move)
        if len(moves_trump_suit)!=0:
            move = self.rng.choice(moves_trump_suit)
            return move
        if not state.am_i_leader():
            if leader_move.is_trump_exchange():
                leader_suit = move.cards[0].suit
            else:
                leader_move = leader_move.as_regular_move()
                leader_suit = move.card.suit
            for move in list(moves):
                if move.is_trump_exchange():
                    suit = move.cards[0].suit
                else:
                    move = move.as_regular_move()
                    suit = move.card.suit
                if suit == leader_suit:
                    moves_same_suit.append(move)
            if len(moves_same_suit)!=0:
                move = self.rng.choice(moves_same_suit)
                return move
        best_score = float('-inf')
        best_move = None
        for move in list(moves):
            if move.is_trump_exchange():
                score = scorer.rank_to_points(move.cards[0].rank)
            else:
                move = move.as_regular_move()
                score = scorer.rank_to_points(move.card.rank)
            if score > best_score:
                best_score = score
                best_move = move
            
        return best_move

    def __repr__(self) -> str:
        return f"BullyBot(seed={self.seed})"
