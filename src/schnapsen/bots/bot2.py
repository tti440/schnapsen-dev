import random
from typing import Optional
from src.schnapsen.game import Bot, PlayerPerspective, Move, SchnapsenTrickScorer
from src.schnapsen.deck import Suit
class SecondBot(Bot):
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.my_last_move_suit: Optional[Suit] = None
    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move], ) -> Move:
        # get all my available moves
        valid_moves = state.valid_moves()
        #  make a list that contains all moves we are allowed to do, given the assignment announcement
        next_move_choices: list[Move] = []
        selected_move: Move
        # "If your score of the bot is lower than the opponent"
        # get opponent's score
        opponents_score = state.get_opponent_score().direct_points
        # get my score
        my_score = state.get_opponent_score().direct_points
        # if my score is lower than the opponent's
        if my_score < opponents_score:
            # for every valid move I can in principle play at this point of the game following the rules
            for valid_move in valid_moves:
                # "Try to play a marriage or trump exchange (if this is a valid move)"
                # if this move is either a trump exchange or a marriage
                if valid_move.is_trump_exchange() or valid_move.is_marriage():
                    next_move_choices.append(valid_move)
        # Elsif tries to play the same suit it played in the previous turn (if thatis a valid move),  if there are multiple
        # if this bot has played a move before (because during first move, the field "self.my_last_move" is None)
        elif self.my_last_move_suit is not None:
            # we get the suit of the previous move
            previous_move_suit = self.my_last_move_suit
            # create an instance object of a SchnapsenTrickScorer Class, that allows us to get the rank of Cards.
            schnapsen_trick_scorer = SchnapsenTrickScorer()
            # Keep the actions with the lowest point as long as it has the same suit.
            # Setting lowest_points it to something higher than the range of valueswe will see, so that it will certainly change
            lowest_points: int = 100
            lowest_points_move: Optional[Move] = None
            for valid_move in valid_moves:
                # if the move has the same suit with our previous move
                if valid_move.cards[0].suit == previous_move_suit:
                    # get the points of the move
                    # points of moves are defined by their card played.
                    # For marriage, it's the queen, for Trump exchange its 0, sinceno card is actually played
                    move_points: int
                    if valid_move.is_trump_exchange():
                        move_points = 0
                    elif valid_move.is_marriage():
                        move_points = schnapsen_trick_scorer.rank_to_points(
                            valid_move.as_marriage().queen_card.rank)
                    else:
                        move_points = schnapsen_trick_scorer.rank_to_points(
                            valid_move.as_regular_move().card.rank)
                    # if this move has the lowest points checked so far, we set itto be the selected on to play
                    if move_points <= lowest_points:
                        lowest_points = move_points
                        lowest_points_move = valid_move
            # if we found at least one move with the same suit as our previous move, then we want to play that
            if lowest_points_move is not None:
                next_move_choices = [lowest_points_move]
            else:
                next_move_choices = []
        # if the previous conditions were met, but did not result in a valid action
        # (e.g. Maybe the player played a suit before, but we do not have another card with the same suit at hand)
        # then we go to the third and last condition of the bot behaviour
        # "Else, it plays a random valid move (which is not a marriage or trump exchange)."
        if len(next_move_choices) == 0:
            #     then, all valid action can be played
            valid_moves = state.valid_moves()
            for move in valid_moves:
                if move.is_regular_move():
                    next_move_choices.append(move)
        # we randomly sample one move from all the moves that we are allowed to play following the bot's logic.
        selected_move = self.rng.choice(next_move_choices)
        # we also store it suit in the bot, so that we can access in the future the"last move played"
        self.my_last_move_suit = selected_move.cards[0].suit
        return selected_move
    def __repr__(self) -> str:
        return f"SecondBot  "


