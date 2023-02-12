import random
import pathlib

from typing import Optional

import click
from src.schnapsen.bots.rdeep_ML import RdeepMLBot
from src.schnapsen.bots import MLDataBot, train_ML_model, MLPlayingBot, RandBot, BullyBot
from src.schnapsen.bots.example_bot import ExampleBot

from src.schnapsen.game import (Bot, Move, PlayerPerspective,
                            SchnapsenGamePlayEngine, Trump_Exchange)
from src.schnapsen.twenty_four_card_schnapsen import \
    TwentyFourSchnapsenGamePlayEngine
from src.schnapsen.bots.bot2 import SecondBot
from src.schnapsen.bots.rdeep import RdeepBot
from binomial_experiment import binom_experiment

@click.group()
def main() -> None:
    """Various Schnapsen Game Examples"""

def play_games_and_return_stats(engine: SchnapsenGamePlayEngine, bot1: Bot, bot2: Bot, number_of_games: int) -> int:
    """
    Play number_of_games games between bot1 and bot2, using the SchnapsenGamePlayEngine, and return how often bot1 won.
    Prints progress.
    """
    bot1_wins: int = 0
    lead, follower = bot1, bot2
    for i in range(1, number_of_games + 1):
        if i % 2 == 0:
            # swap bots so both start the same number of times
            lead, follower = follower, lead
        winner, _, _ = engine.play_game(lead, follower, random.Random(i))
        if winner == bot1:
            bot1_wins += 1
        if i % 500 == 0:
            print(f"Progress: {i}/{number_of_games}")
    return bot1_wins


@main.command()
def random_game() -> None:
    engine = SchnapsenGamePlayEngine()
    bot1 = RandBot(12112121)
    bot2 = RandBot(464566)
    for i in range(1000):
        winner_id, game_points, score = engine.play_game(bot1, bot2, random.Random(i))
        print(f"Game ended. Winner is {winner_id} with {game_points} points, score {score}")


class NotificationExampleBot(Bot):

    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        moves = state.valid_moves()
        return moves[0]

    def notify_game_end(self, won: bool, state: PlayerPerspective) -> None:
        print(f'result {"win" if won else "lost"}')
        print(f'I still have {len(state.get_hand())} cards left')

    def notify_trump_exchange(self, move: Trump_Exchange) -> None:
        print(f"That trump exchanged! {move.jack}")


@main.command()
def notification_game() -> None:
    engine = TwentyFourSchnapsenGamePlayEngine()
    bot1 = NotificationExampleBot()
    bot2 = RandBot(464566)
    engine.play_game(bot1, bot2, random.Random(94))


class HistoryBot(Bot):
    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        history = state.get_game_history()
        print(f'the initial state of this game was {history[0][0]}')
        moves = state.valid_moves()
        return moves[0]


@main.command()
def try_example_bot_game() -> None:
    engine = SchnapsenGamePlayEngine()
    bot1 = ExampleBot()
    bot2 = RandBot(464566)
    winner, points, score = engine.play_game(bot1, bot2, random.Random(1))
    print(f"Winner is: {winner}, with {points} points!")


@main.command()
def rdeep_game() -> None:
    bot1: Bot
    bot2: Bot
    engine = SchnapsenGamePlayEngine()
    rdeep = bot1 = RdeepBot(num_samples=12, depth=6, rand=random.Random(4564654644))
    bot2 = RandBot(464566)
    wins = 0
    amount = 100
    for game_number in range(1, amount + 1):
        if game_number % 2 == 0:
            bot1, bot2 = bot2, bot1
        winner_id, _, _ = engine.play_game(bot1, bot2, random.Random(game_number))
        if winner_id == rdeep:
            wins += 1
        if game_number % 10 == 0:
            print(f"won {wins} out of {game_number}")

@main.command()
def rdeepML_game() -> None:
    bot1: Bot
    bot2: Bot
    engine = SchnapsenGamePlayEngine()
    rdeep = bot1 = RdeepMLBot(num_samples=8, depth=6, rand=random.Random(4564654644))
    bot2 = RandBot(random.Random(464566))
    wins = 0
    amount = 100
    for game_number in range(1, amount + 1):
        if game_number % 2 == 0:
            bot1, bot2 = bot2, bot1
        winner_id, _, _ = engine.play_game(bot1, bot2, random.Random(game_number))
        if winner_id == rdeep:
            wins += 1
        if game_number % 10 == 0:
            print(f"won {wins} out of {game_number}")
            
            
@main.group()
def ml() -> None:
    """Commands for the ML bot"""


@ml.command()
def create_replay_memory_dataset() -> None:
    # define replay memory database creation parameters
    num_of_games: int = 10000
    replay_memory_dir: str = 'ML_replay_memories'
    replay_memory_filename: str = 'RdeepBot_RdeepBot_10k_games_for_rollout.txt'
    replay_memory_location = pathlib.Path(replay_memory_dir) / replay_memory_filename

    #bot_1_behaviour: Bot = SecondBot(random.Random(5234243))
    bot_1_behaviour= RdeepBot(num_samples=6, depth=6, rand=random.Random(5234243))
    # bot_1_behaviour: Bot = RdeepBot(num_samples=4, depth=4, rand=random.Random(4564654644))
    #bot_2_behaviour: Bot = SecondBot(random.Random(54354))
    bot_2_behaviour= RdeepBot(num_samples=6, depth=6, rand=random.Random(54354))
    # bot_2_behaviour: Bot = RdeepBot(num_samples=4, depth=4, rand=random.Random(68438))
    delete_existing_older_dataset = False

    # check if needed to delete any older versions of the dataset
    if delete_existing_older_dataset and replay_memory_location.exists():
        print(f"An existing dataset was found at location '{replay_memory_location}', which will be deleted as selected.")
        replay_memory_location.unlink()

    # in any case make sure the directory exists
    replay_memory_location.parent.mkdir(parents=True, exist_ok=True)

    # create new replay memory dataset, according to the behaviour of the provided bots and the provided random seed
    engine = SchnapsenGamePlayEngine()
    replay_memory_recording_bot_1 = MLDataBot(bot_1_behaviour, replay_memory_location=replay_memory_location)
    replay_memory_recording_bot_2 = MLDataBot(bot_2_behaviour, replay_memory_location=replay_memory_location)
    for i in range(1, num_of_games + 1):
        if i % 500 == 0:
            print(f"Progress: {i}/{num_of_games}")
        engine.play_game(replay_memory_recording_bot_1, replay_memory_recording_bot_2, random.Random(i))
    print(f"Replay memory dataset recorder for {num_of_games} games.\nDataset is stored at: {replay_memory_location}")


@ml.command()
def train_model() -> None:
    # directory where the replay memory is saved
    replay_memory_filename: str = 'RdeepBot_RdeepBot_10k_games_for_rollout.txt'
    # filename of replay memory within that directory
    replay_memories_directory: str = 'ML_replay_memories'
    # Whether to train a complicated Neural Network model or a simple one.
    # Tips: a neural network usually requires bigger datasets to be trained on, and to play with the parameters of the model.
    # Feel free to play with the hyperparameters of the model in file 'ml_bot.py', function 'train_ML_model',
    # under the code of body of the if statement 'if use_neural_network:'
    replay_memory_location = pathlib.Path(replay_memories_directory) / replay_memory_filename
    model_name: str = 'New_Rdeep_model'
    model_dir: str = "ML_models"
    model_location = pathlib.Path(model_dir) / model_name
    overwrite: bool = False

    if overwrite and model_location.exists():
        print(f"Model at {model_location} exists already and will be overwritten as selected.")
        model_location.unlink()

    train_ML_model(replay_memory_location=replay_memory_location, model_location=model_location,
                   model_class='NN')


@ml.command()
def try_bot_game() -> None:
    engine = SchnapsenGamePlayEngine()
    model_dir: str = 'ML_models'
    model_name: str = 'simple_model'
    model_location = pathlib.Path(model_dir) / model_name
    bot1: Bot = MLPlayingBot(model_location=model_location)
    bot2: Bot = RandBot(464566)
    number_of_games: int = 10000

    # play games with altering leader position on first rounds
    ml_bot_wins_against_random = play_games_and_return_stats(engine=engine, bot1=bot1, bot2=bot2, number_of_games=number_of_games)
    print(f"The ML bot with name {model_name}, won {ml_bot_wins_against_random} times out of {number_of_games} games played.")


@main.command()
def game_24() -> None:
    engine = TwentyFourSchnapsenGamePlayEngine()
    bot1 = RandBot(12112121)
    bot2 = RandBot(464566)
    for i in range(1000):
        winner_id, game_points, score = engine.play_game(bot1, bot2, random.Random(i))
        print(f"Game ended. Winner is {winner_id} with {game_points} points, score {score}")

@main.command()
def experiment_rdeep():
    binom_experiment(100, 6, 6)
    
if __name__ == "__main__":
    main()