from src.schnapsen.bots.gui import SchnapsenServer
from src.schnapsen.bots.rand import RandBot
from src.schnapsen.bots.bully import BullyBot
from src.schnapsen.bots.bot2 import Bot2
from src.schnapsen.game import SchnapsenGamePlayEngine
import random

if __name__ == "__main__":
    engine = SchnapsenGamePlayEngine()
    with SchnapsenServer() as s:
        # Change bot1 to BUllyBot 
        bot1 = BullyBot(464566)
        bot2 = s.make_gui_bot(name="mybot2")
        # bot1 = s.make_gui_bot(name="mybot1")
        engine.play_game(bot1, bot2, random.Random(100))
