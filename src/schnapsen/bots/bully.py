import random
from typing import Optional
from src.schnapsen.game import Bot, PlayerPerspective, Move, SchnapsenTrickScorer, RegularMove
from src.schnapsen.deck import Card, Suit
class BullyBot(Bot):
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move], ) -> Move:
        # The bully bot only plays valid moves.
        # get all valid moves
        my_valid_moves = state.valid_moves()
        trump_suit_moves: list[Move] = []
        # get the trump suit
        trump_suit: Suit = state.get_trump_suit()
        # get all my valid moves that have the same suit with trump suit.
        for move in my_valid_moves:
            cards_of_move: list[Card] = move.cards
            # get 1st of the list of cards of this move (in case of multiple -> Marriage)
            card_of_move: Card = cards_of_move[0]
            if card_of_move.suit == trump_suit:
                trump_suit_moves.append(move)
        # If you have cards of the trump suit, play one of them at random
        if len(trump_suit_moves) > 0:
            random_trump_suit_move = self.rng.choice(trump_suit_moves)
            return random_trump_suit_move
        # Else, if you are the follower and you have cards of the same suit as the opponent, play one of these at random.
        if not state.am_i_leader():
            assert leader_move is not None
            leader_suit: Suit = leader_move.cards[0].suit
            leaders_suit_moves: list[Move] = []
            # get all my valid moves that have the same suit with leader suit.
            for move in my_valid_moves:
                cards_of_move = move.cards
                # get 1st of the list of cards of this move (in case of multiple ->Mariage)
                card_of_move = cards_of_move[0]
                if card_of_move.suit == leader_suit:
                    leaders_suit_moves.append(move)
            if len(leaders_suit_moves) > 0:
                random_leader_suit_move = self.rng.choice(leaders_suit_moves)
                return random_leader_suit_move
        # Else, play one of your cards with the highest rank
        # get the list of cards in my hand
        my_hand_cards: list[Card] = state.get_hand().cards
        # create an instance object of a SchnapsenTrickScorer Class, that allows usto get the rank of Cards.
        schnapsen_trick_scorer = SchnapsenTrickScorer()
        # we set the highest rank to something negative, forcing it to change with the first comparison, since all scores are positive
        highest_card_score: int = -1
        card_with_highest_score: Optional[Card] = None
        for card in my_hand_cards:
            card_score = schnapsen_trick_scorer.rank_to_points(card.rank)
            if card_score > highest_card_score:
                highest_card_score = card_score
                card_with_highest_score = card
        # if our logic above was correct, this can never be None. We double check to make sure.
        assert card_with_highest_score is not None
        # We now create a move out of this card. Note that here we do not return a move from a call to valid_moves.
        # An alternative implementaiton would first have taken all valid moves and subsequently filtered these down to
        # the list of valid cards. Then, we would have found the one with the highest score from that.
        move_of_card_with_highest_score = RegularMove(card_with_highest_score)
        # We can double check that this is a valid move like this.
        assert move_of_card_with_highest_score in my_valid_moves
        return move_of_card_with_highest_score
    def __repr__(self) -> str:
        return f"BullyBot "

