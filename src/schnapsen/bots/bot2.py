import random
from typing import Optional
from src.schnapsen.game import Bot, PlayerPerspective, Move, SchnapsenTrickScorer, ExchangeFollowerPerspective 

class Bot2(Bot):
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(self.seed)
        self.previous_move = None
    def get_move(
        self,
        state: PlayerPerspective,
        leader_move: Optional[Move],
    ) -> Move:
        scorer = SchnapsenTrickScorer()
        moves = state.valid_moves()
        self.rng.shuffle(moves)
        if state.get_my_score().direct_points < state.get_opponent_score().direct_points:
            for move in list(moves):
                if move.is_marriage() or move.is_trump_exchange():
                    self.previous_move = move
                    return move
                
        if self.previous_move != None:
            if self.previous_move.is_trump_exchange():
                previous_suit = self.previous_move.cards[0].suit
            else:
                move = self.previous_move.as_regular_move()
                previous_suit = move.card.suit
            moves_same_suit = []
            for move in list(moves):
                if move.is_trump_exchange():
                    suit = move.cards[0].suit
                else:
                    suit = move.as_regular_move().card.suit
                if suit == previous_suit:
                    moves_same_suit.append(move)
            lowest_score = float('inf')
            best_move = None
            if len(moves_same_suit)!=0:
                for move in moves_same_suit:
                    if move.is_trump_exchange():
                        rank = move.cards[0].rank
                    else:
                        rank = move.as_regular_move().card.rank
                    score = scorer.rank_to_points(rank)
                    if score < lowest_score:
                        lowest_score = score
                        best_move = move
                self.previous_move = best_move
                return best_move
        
        move = self.rng.choice(list(moves))
        while move.is_marriage() or move.is_trump_exchange():
            move = self.rng.choice(list(moves))
        self.previous_move = move 
        return move
    
    def __repr__(self) -> str:
        return f"Bot2(seed={self.seed})"   

