import pathlib
from typing import Optional, cast
from src.schnapsen.game import Bot, PlayerPerspective, Move, GameState, GamePlayEngine, Trick
from random import Random
from src.schnapsen.bots import MLPlayingBot, RdeepBot, RandBot
from src.schnapsen.bots.bot2 import SecondBot
from src.schnapsen.bots.bully import BullyBot
import joblib
import numpy as np

class RdeepMLBot(Bot):
    def __init__(self, num_samples: int, depth: int, rand: Random) -> None:
        """
        Create a new rdeep bot.

        :param num_samples: how many samples to take per move
        :param depth: how deep to sample
        :param rand: the source of randomness for this Bot
        """
        assert num_samples >= 1, f"we cannot work with less than one sample, got {num_samples}"
        assert depth >= 1, f"it does not make sense to use a dept <1. got {depth}"
        self.__num_samples = num_samples
        self.__depth = depth
        self.__rand = rand
        self.previous_state = []
        self.count = []
        self.KNN_count = [0,0,0,0]
    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        # get the list of valid moves, and shuffle it such
        # that we get a random move of the highest scoring
        # ones if there are multiple highest scoring moves.
        moves = state.valid_moves()
        self.__rand.shuffle(moves)
        best_score = float('-inf')
        best_move = None
        model_path = self.predict_opponent(state)
        moves_count = 0
        for move in moves:
            sum_of_scores = 0.0
            total_count = 0
            for _ in range(self.__num_samples):
                gamestate, count = state.make_assumption_ML(leader_move=leader_move, rand=self.__rand, my_move=move)
                if count is not None:
                    total_count += count
                score = self.__evaluate(model_path, gamestate, state.get_engine(), leader_move, move)
                sum_of_scores += score
            if count is not None:
                total_count = total_count/self.__num_samples
                moves_count += total_count
            average_score = sum_of_scores / self.__num_samples
            if average_score > best_score:
                best_score = average_score
                best_move = move
        assert best_move is not None
        if count is not None:
            self.count += [moves_count/len(moves)]
        return best_move

    def __evaluate(self, model_path, gamestate: GameState, engine: GamePlayEngine, leader_move: Optional[Move], my_move: Move) -> float:
        """
        Evaluates the value of the given state for the given player
        :param state: The state to evaluate
        :param player: The player for whom to evaluate this state (1 or 2)
        :return: A float representing the value of this state for the given player. The higher the value, the better the
                state is for the player.
        """
        me: Bot
        leader_bot: Bot
        follower_bot: Bot
        if model_path is None:
            oppoenet = RandBot(rand=self.__rand)
        else:
            oppoenet = MLPlayingBot(pathlib.Path(model_path))
        if leader_move:
            # we know what the other bot played
            leader_bot = FirstFixedMoveThenBaseBot(oppoenet, leader_move)
            # I am the follower
            me = follower_bot = FirstFixedMoveThenBaseBot(MLPlayingBot(pathlib.Path("ML_models/New_Rdeep_model")), my_move)
        else:
            # I am the leader bot
            me = leader_bot = FirstFixedMoveThenBaseBot(MLPlayingBot(pathlib.Path("ML_models/New_Rdeep_model")), my_move)
            # We assume the other bot just random
            follower_bot = oppoenet

        new_game_state, _ = engine.play_at_most_n_tricks(game_state=gamestate, new_leader=leader_bot, new_follower=follower_bot, n=self.__depth)

        if new_game_state.leader.implementation is me:
            my_score = new_game_state.leader.score.direct_points
            opponent_score = new_game_state.follower.score.direct_points
        else:
            my_score = new_game_state.follower.score.direct_points
            opponent_score = new_game_state.leader.score.direct_points

        heuristic = my_score / (my_score + opponent_score)
        return heuristic

    def predict_opponent(self, state: PlayerPerspective):
        game_history: list[tuple[PlayerPerspective, Trick]] = cast(list[tuple[PlayerPerspective, Trick]], state.get_game_history())
        if len(game_history) > 1:
            prev = game_history[-2]
            round_player_perspective, round_trick = prev
            if round_trick.is_trump_exchange():
                leader_move = round_trick.exchange
                follower_move = None
            else:
                leader_move = round_trick.leader_move
                follower_move = round_trick.follower_move
            # we do not want this representation to include actions that followed. So if this agent was the leader, we ignore the followers move
            if round_player_perspective.am_i_leader():
                follower_move = None
            state_actions_representation = state.create_state_and_actions_vector_representation(
                state=round_player_perspective, leader_move=leader_move, follower_move=follower_move)
            self.previous_state += [state_actions_representation]
            model = joblib.load("ML_models/KNN_model")
            pred = list(model.predict(self.previous_state))
            index = max(set(pred), key = pred.count)
            self.KNN_count[index] += 1
            if index == 0:
                model_path = "ML_models/random_model"
            elif index == 1:
                model_path = "ML_models/bully_model"
            elif index == 2:
                model_path = "ML_models/New_Rdeep_model"
            elif index == 3:
                model_path = "ML_models/2ndBot_model"
        else:
            model_path = None
        return model_path
    
class RandBot(Bot):

    def __init__(self, rand: Random) -> None:
        self.rand = rand

    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        return self.rand.choice(state.valid_moves())


class FirstFixedMoveThenBaseBot(Bot):
    def __init__(self, base_bot: Bot, first_move: Move) -> None:
        self.first_move = first_move
        self.first_move_played = False
        self.base_bot = base_bot

    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        if not self.first_move_played:
            self.first_move_played = True
            return self.first_move
        return self.base_bot.get_move(state=state, leader_move=leader_move)
