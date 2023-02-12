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
from statsmodels.stats.proportion import proportions_ztest

def prop_ztest(bot, amount, samples=6, depth=6):
    bot1: Bot
    bot2: Bot
    engine = SchnapsenGamePlayEngine()
    win_rdeepML = 0
    win_rdeep = 0
    for game_number in range(1, amount + 1):
        #rdeep_ML = bot1 = RdeepMLBot(num_samples=samples, depth=depth, rand=random.Random(4564654644))
        rdeep_ML = bot1 = RdeepMLBot(num_samples=samples, depth=depth, rand=random.Random(4564654644))
        bot2 = bot
        if game_number % 2 == 0:
            bot1, bot2 = bot2, bot1
        winner_id, _, _ = engine.play_game(bot1, bot2, random.Random(game_number))
        if winner_id == rdeep_ML:
            win_rdeepML += 1
        if game_number % 50 == 0:
            print(str(game_number) + " Game has finished")
    for game_number in range(1, amount + 1):
        #rdeep_ML = bot1 = RdeepMLBot(num_samples=samples, depth=depth, rand=random.Random(4564654644))
        rdeep = bot1 = RdeepBot(num_samples=6, depth=6, rand=random.Random(4564654644))
        bot2 = bot
        if game_number % 2 == 0:
            bot1, bot2 = bot2, bot1
        winner_id, _, _ = engine.play_game(bot1, bot2, random.Random(game_number))
        if winner_id == rdeep:
            win_rdeep += 1
        if game_number % 50 == 0:
            print(str(game_number) + " Game has finished")
    result, p_value = proportions_ztest([win_rdeepML,win_rdeep], [200,200], alternative = "larger")
    return result, p_value, win_rdeep, win_rdeepML
    