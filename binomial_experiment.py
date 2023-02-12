import random
import pathlib

from typing import Optional

import click
from src.schnapsen.bots.rdeep_ML import RdeepMLBot
from src.schnapsen.bots import MLPlayingBot, RandBot, BullyBot, RdeepBot, SecondBot

from src.schnapsen.game import (Bot, Move, PlayerPerspective,
                            SchnapsenGamePlayEngine, Trump_Exchange)
from src.schnapsen.twenty_four_card_schnapsen import \
    TwentyFourSchnapsenGamePlayEngine
import pandas as pd
from scipy.stats import binomtest

def binom_experiment(amount, samples, depth):
    bot1: Bot
    bot2: Bot
    engine = SchnapsenGamePlayEngine()
    win = 0
    for game_number in range(1, amount + 1):
        #rdeep_ML = bot1 = RdeepMLBot(num_samples=samples, depth=depth, rand=random.Random(4564654644))
        rdeep_ML = bot1 = RdeepBot(num_samples=6, depth=6, rand=random.Random(4564654644))
        bot2 = RdeepBot(num_samples=6, depth=6, rand=random.Random(4564654644))
        if game_number % 2 == 0:
            bot1, bot2 = bot2, bot1
        winner_id, _, _ = engine.play_game(bot1, bot2, random.Random(game_number))
        if winner_id == rdeep_ML:
            win += 1
        if game_number % 50 == 0:
            print(str(game_number) + " Game has finished")
    result = binomtest(win, n=amount, p=0.5, alternative='greater')
    p_value = result.pvalue
    return result, p_value
    