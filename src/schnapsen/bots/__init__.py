"""Create a bot in a separate .py and import them here, so that one can simply import
it by from schnapsen.bots import MyBot.
"""
from .rand import RandBot
from .alphabeta import AlphaBetaBot
from .rdeep import RdeepBot
from .ml_bot import MLDataBot, MLPlayingBot, train_ML_model
from .gui.guibot import SchnapsenServer
from .rdeep_ML import RdeepMLBot
from .bot2 import SecondBot
from .bully import BullyBot
__all__ = ["BullyBot", "SecondBot", "RdeepMLBot", "RandBot", "AlphaBetaBot", "RdeepBot", "MLDataBot", "MLPlayingBot", "train_ML_model", "SchnapsenServer"]
