from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from random import Random
from typing import Iterable, List, Optional, Tuple, Union, cast, Any
from .deck import CardCollection, OrderedCardCollection, Card, Rank, Suit
import itertools


class Bot(ABC):
    """
    The Bot baseclass. Derive your own bots from this class and implement the get_move method to use it in games.

    Besides the get_move method, it is also possible to override notify_trump_exchange and notify_game_end to get notified when these events happen.
    """
    @abstractmethod
    def get_move(self, state: 'PlayerPerspective', leader_move: Optional['Move']) -> 'Move':
        """
        Get the move this Bot wants to play.
        If this Bot is leading, the leader_move will be None. If this both is following, the leader_move will contain the move the opponent just played
        """
        pass

    def notify_trump_exchange(self, move: 'Trump_Exchange') -> None:
        """
        Overide this method to get notified about trump exchanges. Note that this only notifies about the other bots exchanges.

        :param move: the Trump Exchange move that was played.
        """
        pass

    def notify_game_end(self, won: bool, state: 'PlayerPerspective') -> None:
        """
        Override this method to get notified about the end of the game.

        :param won: Did this bot win the game?
        :param state: The final state of the game.
        """
        pass


class Move(ABC):
    """
    A single move during a game. There are several types of move possible: normal moves, trump exchanges, and marriages. They are implmented in classes inheriting from this class.
    """

    cards: List[Card]  # implementation detail: The creation of this list is defered to the derived classes in _cards()
    """The cards played in this move"""

    def is_marriage(self) -> bool:
        """
        Is this Move a marriage?

        :returns: a bool indicating whether this move is a marriage
        """
        return False

    def is_trump_exchange(self) -> bool:
        """
        Is this Move a trump exchange move?

        :returns: a bool indicating whether this move is a trump exchange
        """
        return False

    def __getattribute__(self, __name: str) -> Any:
        if __name == "cards":
            # We call the method to compute the card list
            return object.__getattribute__(self, "_cards")()
        return object.__getattribute__(self, __name)

    @abstractmethod
    def _cards(self) -> Iterable[Card]:
        pass


@dataclass(frozen=True)
class Trump_Exchange(Move):
    """A move that implements the exchange of the trump card for a Jack of the same suit."""

    jack: Card
    """The Jack which will be placed at the bottom of the Talon"""

    def __post_init__(self) -> None:
        assert self.jack.rank is Rank.JACK

    def is_trump_exchange(self) -> bool:
        return True

    def _cards(self) -> Iterable[Card]:
        return [self.jack]

    def __repr__(self) -> str:
        return f"Trump_Exchange(jack={self.jack})"


@dataclass(frozen=True)
class RegularMove(Move):
    """A regular move in the game"""

    card: Card
    """The card which is played"""

    def _cards(self) -> Iterable[Card]:
        return [self.card]

    @staticmethod
    def from_cards(cards: Iterable[Card]) -> Iterable[Move]:
        """Create an iterable of Moves from an iterable of cards."""
        return [RegularMove(card) for card in cards]

    def as_regular_move(self) -> 'RegularMove':
        return self

    def __repr__(self) -> str:
        return f"RegularMove(card={self.card})"


@dataclass(frozen=True)
class Marriage(Move):
    """
    A Move representing a marriage in the game. This move has two cards, a king and a queen of the same suit.
    Right after the marriage is played, the player must play either the queen or the king.
    Because it can only be beneficial to play the queen, it is chosen automatically.
    This Regular move is part of this Move already and does not have to be played separatly.
    """
    queen_card: Card
    """The queen card of this marriage"""
    king_card: Card
    """The king card of this marriage"""
    suit: Suit = field(init=False, repr=False, hash=False)
    """The suit of this marriage, gets derived from the suit of the queen and king."""

    def __post_init__(self) -> None:
        assert self.queen_card.rank is Rank.QUEEN
        assert self.king_card.rank is Rank.KING
        assert self.queen_card.suit == self.king_card.suit
        object.__setattr__(self, "suit", self.queen_card.suit)

    def is_marriage(self) -> bool:
        return True

    def as_regular_move(self) -> RegularMove:
        # TODO this limits you to only have the queen to play after a marriage, while in general you would ahve a choice
        return RegularMove(self.queen_card)

    def _cards(self) -> Iterable[Card]:
        return [self.queen_card, self.king_card]

    def __repr__(self) -> str:
        return f"Marriage(queen_card={self.queen_card}, king_card={self.king_card})"


class Hand(CardCollection):
    """Representing the cards in the hand of a player. These are the cards which the player can see and which he can play with in the turn."""

    def __init__(self, cards: Iterable[Card], max_size: int = 5) -> None:
        """
        Create a hand containing the cards.

        :param cards: The cards to be added to the hand
        :param max_size: The maximum number of cards the hand can contain. If the number of cards goes beyond, an Exception is raised.
        """
        self.max_size = max_size
        cards = list(cards)
        assert len(cards) <= max_size, f"The number of cards {len(cards)} is larger than the maximum number fo allowed cards {max_size}"
        self.cards = cards

    def remove(self, card: Card) -> None:
        """Remove one occurence of the card from this hand"""
        try:
            self.cards.remove(card)
        except ValueError:
            raise Exception(f"Trying to remove a card from the hand which is not in the hand. Hand is {self.cards}, trying to remove {card}")

    def add(self, card: Card) -> None:
        """
        Add a card to the Hand

        :param card:  The card to be added to the hand
        """
        assert len(self.cards) < self.max_size, "Adding one more card to the hand will cause a hand with too many cards"
        self.cards.append(card)

    def has_cards(self, cards: Iterable[Card]) -> bool:
        """
        Are all the cards contained in this Hand?

        :param cards: An iterable of cards which need to be checked
        :returns: Whether all cards in the provided iterable are in this Hand
        """
        return all([card in self.cards for card in cards])

    def copy(self) -> 'Hand':
        """
        Create a deep copy of this Hand

        :returns: A deep copy of this hand. Changes to the original will not affect the copy and vice versa.
        """
        return Hand(list(self.cards), max_size=self.max_size)

    def is_empty(self) -> bool:
        """
        Is the Hand emoty?

        :returns: A bool indicating whether the hand is empty
        """
        return len(self.cards) == 0

    def get_cards(self) -> List[Card]:
        return list(self.cards)

    def filter_suit(self, suit: Suit) -> Iterable[Card]:
        results = [card for card in self.cards if card.suit is suit]
        return results

    def filter_rank(self, rank: Rank) -> Iterable[Card]:
        results = [card for card in self.cards if card.rank is rank]
        return results

    def __repr__(self) -> str:
        return f"Hand(cards={self.cards}, max_size={self.max_size})"


class Talon(OrderedCardCollection):

    def __init__(self, cards: Iterable[Card], trump_suit: Optional[Suit] = None) -> None:
        """
        The cards of the Talon. The last card of the iterable is the bottommost card.
        The first one is the top card (which will be taken is a card is drawn)
        The Trump card is at the bottom of the Talon.
        The trump_suit can also be specified explicitly, which is important when the Talon is empty.
        If the trump_suit is specified and there are cards, then the suit of the bottommost card must be the same.

        :param cards: The cards to be put on this talon
        :param trump_suit: The trump suit of the Talon, important if there are no more cards to be taken.
        """
        if cards:
            trump_card_suit = list(cards)[-1].suit
            assert not trump_suit or trump_card_suit == trump_suit, "If the trump suit is specified, and there are cards on the talon, the suit must be the same!"
            self.__trump_suit = trump_card_suit
        else:
            assert trump_suit
            self.__trump_suit = trump_suit

        super().__init__(cards)

    def copy(self) -> 'Talon':
        # We do not need to make a copy of the cards as this happend in the constructor of Talon.
        return Talon(self._cards, self.__trump_suit)

    def trump_exchange(self, new_trump: Card) -> Card:
        """
        perfom a trump-jack exchange. The card to be put as the trump card must be a Jack of the same suit.
        As a result, this Talon changed: the old trump is removed and the new_trump is at the bottom of the Talon

        We also require that there must be two cards on the Talon, which is always the case in a normal game of Schnapsen

        :param new_trump: The card to be put. It must be a Jack of the same suit as the card at the bottom

        """
        assert new_trump.rank is Rank.JACK
        assert len(self._cards) >= 2
        assert new_trump.suit is self._cards[-1].suit
        old_trump = self._cards.pop(len(self._cards) - 1)
        self._cards.append(new_trump)
        return old_trump

    def draw_cards(self, amount: int) -> Iterable[Card]:
        """Draw a card from this Talon. This does not change the talon, btu rather returns a talon with the change applied and the card drawn"""
        assert len(self._cards) >= amount, f"There are only {len(self._cards)} on the Talon, but {amount} cards are requested"
        draw = self._cards[:amount]
        self._cards = self._cards[amount:]
        return draw

    def trump_suit(self) -> Suit:
        """Return the suit of the trump card, i.e., the bottommost card.
        This still works, even when the Talon has become empty.
        """
        return self.__trump_suit

    def trump_card(self) -> Optional[Card]:
        """Returns the current trump card, i.e., the bottommost card.
        Or None in case this Talon is empty
        """
        if len(self._cards) > 0:
            return self._cards[-1]
        else:
            return None

    def __repr__(self) -> str:
        return f"Talon(cards={self._cards}, trump_suit={self.__trump_suit})"


@dataclass(frozen=True)
class Trick(ABC):
    """
    A complete trick. This is, the move of the leader and if that was not an exchange, the move of the follower.
    """

    cards: Iterable[Card] = field(init=False, repr=False, hash=False)
    """All cards used as part of this trick. This includes cards used in marriages"""

    @abstractmethod
    def is_trump_exchange(self) -> bool:
        """
        Returns True if this is a trump exchange

        :returns: True in case this was a trump exchange
        """

    @abstractmethod
    def as_partial(self) -> 'PartialTrick':
        """
        Returns the first part of this trick. Raises an Exceptption if this is not a Trick with two parts
        """

    def __getattribute__(self, __name: str) -> Any:
        if __name == "cards":
            # We call the method to compute the card list
            return object.__getattribute__(self, "_cards")()
        return object.__getattribute__(self, __name)

    @abstractmethod
    def _cards(self) -> Iterable[Card]:
        pass


@dataclass(frozen=True)
class ExchangeTrick(Trick):
    exchange: Trump_Exchange
    """A trump exchange by the leading player"""

    def is_trump_exchange(self) -> bool:
        return True

    def as_partial(self) -> 'PartialTrick':
        raise Exception("An Exchange Trick does not have a first part")

    def _cards(self) -> Iterable[Card]:
        return self.exchange.cards


@dataclass(frozen=True)
class PartialTrick:
    """
    A partial trick is the move(s) played by the leading player.
    """
    leader_move: Union[RegularMove, Marriage]
    """The move played by the leader of the trick"""

    def is_trump_exchange(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"PartialTrick(leader_move={self.leader_move})"


@dataclass(frozen=True)
class RegularTrick(Trick, PartialTrick):
    """
    A regular trick, with a move by the leader and a move by the follower
    """
    follower_move: RegularMove
    """The move played by the follower"""

    def is_trump_exchange(self) -> bool:
        return False

    def as_partial(self) -> PartialTrick:
        return PartialTrick(self.leader_move)

    def _cards(self) -> Iterable[Card]:
        return itertools.chain(self.leader_move.cards, self.follower_move.cards)

    def __repr__(self) -> str:
        return f"RegularTrick(leader_move={self.leader_move}, follower_move={self.follower_move})"


@dataclass(frozen=True)
class Score:
    """
    The score of one of the bots. This consists of the current points and potential pending points because of an earlier played marriage.
    Note that the socre object is immutable and supports the `+` operator, so it can be used somewhat as a usual number.
    """
    direct_points: int = 0
    """The current number of points"""
    pending_points: int = 0
    """Points to be applied in the future because of a past marriage"""

    def __add__(self, other: 'Score') -> 'Score':
        """
        Adds two scores together. Direct points and pending points are added separately.

        :param other:  The score to be added to the current one.
        :returns: A new score object with the points of the current score and the other combined
        """
        total_direct_points = self.direct_points + other.direct_points
        total_pending_points = self.pending_points + other.pending_points
        return Score(total_direct_points, total_pending_points)

    def redeem_pending_points(self) -> 'Score':
        """
        Redeem the pending points

        :returns: A new score object with the pending points added to the direct points and the pending points set to zero.
        """
        return Score(direct_points=self.direct_points + self.pending_points, pending_points=0)

    def __repr__(self) -> str:
        return f"Score(direct_points={self.direct_points}, pending_points={self.pending_points})"


class GamePhase(Enum):
    """
    An indicator about the phase of the game. This is used because in Schnapsen, the rules change when the game enters the second phase.
    """
    ONE = 1
    TWO = 2


@dataclass
class BotState:
    """A bot with its implementation and current state in a game"""

    implementation: Bot
    hand: Hand
    score: Score = field(default_factory=Score)
    won_cards: List[Card] = field(default_factory=list)

    def get_move(self, state: 'PlayerPerspective', leader_move: Optional[Move]) -> Move:
        """
        Gets the next move from the bot itself, passing it the state.
        Does a quick check to make sure that the hand has the cards which are played. More advanced checks are performed outside of this call.

        :param state: The PlayerGameState which contains the information on the current state of the game from the perspective of this player
        :returns: The move the both played
        """
        move = self.implementation.get_move(state, leader_move=leader_move)
        # All checks for move are removed from here. There is a chance the implementation returns something wrong, these issues should be captured by the callee, not by this wrapper.
        return move

    def copy(self) -> 'BotState':
        """
        Makes a deep copy of the current state.

        :returns: The deep copy.
        """
        new_bot = BotState(
            implementation=self.implementation,
            hand=self.hand.copy(),
            score=self.score,  # does not need a copy because it is not mutable
            won_cards=list(self.won_cards),
        )
        return new_bot

    def __repr__(self) -> str:
        return f"BotState(implementation={self.implementation}, hand={self.hand}, "\
               f"score={self.score}, won_cards={self.won_cards})"


@dataclass(frozen=True)
class Previous:
    """
    Information about the previous GameState.
    This object can be used to access the history which lead to the current GameState
    """

    state: 'GameState'
    """The previous state of the game. """
    trick: Trick
    """The trick which led to the current Gamestate from the Previous state"""
    leader_remained_leader: bool
    """Did the leader of remain the leader."""


@dataclass
class GameState:
    """
    The current state of the game, as seen by the game engine.
    This contains all information about the positions of the cards, bots, scores, etc.
    The bot must not get direct access to this information because it would allow it to cheat.
    """
    leader: BotState
    """The current leader, i.e., the one who will play the first move in the next trick"""
    follower: BotState
    """The current follower, i.e., the one who will play the second move in the next trick"""
    trump_suit: Suit = field(init=False)
    """The trump suit in this game. This information is also in the Talon."""
    talon: Talon
    """The talon, containing the cards not yet in the hand of the player and the trump card at the bottom"""
    previous: Optional[Previous]
    """The events which led to this GameState, or None, if this is the initial GameState (or previous tricks and states are unknown)"""

    def __getattribute__(self, __name: str) -> Any:
        if __name == "trump_suit":
            # We get it from the talon
            return self.talon.trump_suit()
        return object.__getattribute__(self, __name)

    def copy_for_next(self) -> 'GameState':
        """
        Make a copy of the gamestate, modified such that the previous state is this state, but the previous trick is not filled yet.
        This is used to create a GameState which will be modified to become the next gamestate.
        """
        # We intentionally do no initialize the previous information. It is not known yet
        new_state = GameState(
            leader=self.leader.copy(),
            follower=self.follower.copy(),
            talon=self.talon.copy(),
            previous=None
        )
        return new_state

    def copy_with_other_bots(self, new_leader: Bot, new_follower: Bot) -> 'GameState':
        """
        Make a copy of the gamestate, modified such that the bots are replaced by the provided ones.
        This is used to continue playing an existing GameState with different bots.
        """
        new_state = GameState(
            leader=self.leader.copy(),
            follower=self.follower.copy(),
            talon=self.talon.copy(),
            previous=self.previous
        )
        new_state.leader.implementation = new_leader
        new_state.follower.implementation = new_follower
        return new_state

    def game_phase(self) -> GamePhase:
        """What is the current phase of the game

        :returns: GamePhase.ONE or GamePahse.TWO indicating the current phase
        """
        if self.talon.is_empty():
            return GamePhase.TWO
        else:
            return GamePhase.ONE

    def are_all_cards_played(self) -> bool:
        """Returns True in case the players have played all their cards and the game is has come to an end

        :returns: Wheter all cards have been played
        """
        return self.leader.hand.is_empty() and self.follower.hand.is_empty() and self.talon.is_empty()

    def __repr__(self) -> str:
        return f"GameState(leader={self.leader}, follower={self.follower}, "\
               f"talon={self.talon}, previous={self.previous})"


class PlayerPerspective(ABC):
    """
    The perspective a player has on the state of the game. This only gives access to the partially observable information.
    The Bot gets passed an instance of this class when it gets requested a move by the GamePlayEngine

    This class has several convenience methods to get more information about the current state.
    """

    def __init__(self, state: 'GameState', engine: 'GamePlayEngine') -> None:
        self.__game_state = state
        self.__engine = engine

    def get_engine(self):
        return self.__engine
    @abstractmethod
    def valid_moves(self) -> List[Move]:
        """
        Get a list of all valid moves the bot can play at this point in the game.

        Design note: this could also return an Iterable[Move], but List[Move] was chosen to make the API easier to use.
        """
        pass

    def get_game_history(self) -> list[tuple['PlayerPerspective', Optional[Trick]]]:
        """
        The game history from the perspective of the player. This means all the past PlayerPerspective this bot has seen, and the Tricks played.
        This only provides access to cards the Bot is allowed to see.

        :returns: The PlayerPerspective and Tricks in chronological order, index 0 is the first round played. Only the last Trick will be None.
        The last pair will contain the current PlayerGameState.
        """

        # We reconstruct the history backwards.
        game_state_history: List[Tuple[PlayerPerspective, Optional[Trick]]] = []
        # We first push the current state to the end
        game_state_history.insert(0, (self, None))

        current_leader = self.am_i_leader()
        current = self.__game_state.previous

        while current:
            # If we were leader, and we remained, then we were leader before
            # If we were follower, and we remained, then we were follower before
            # If we were leader, and we did not remain, then we were follower before
            # If we were leader, and we did not remain, then we were leader before
            # This logic gets reflected by the negation of a xor
            current_leader = not current_leader ^ current.leader_remained_leader

            current_player_state: PlayerPerspective
            if current_leader:
                current_player_state = LeaderPerspective(current.state, self.__engine)
            else:  # We are following
                if current.trick.is_trump_exchange():
                    current_player_state = ExchangeFollowerPerspective(current.state, self.__engine)
                else:
                    current_player_state = FollowerPerspective(current.state, self.__engine, current.trick.as_partial().leader_move)
            history_record = (current_player_state, current.trick)
            game_state_history.insert(0, history_record)

            current = current.state.previous
        return game_state_history

    @abstractmethod
    def get_hand(self) -> Hand:
        """Get the cards in the hand of the current player"""
        pass

    @abstractmethod
    def get_my_score(self) -> Score:
        """Get the socre of the current player. The return Score object contains both the direct points and pending points from a marriage."""
        pass

    @abstractmethod
    def get_opponent_score(self) -> Score:
        """Get the socre of the other player. The return Score object contains both the direct points and pending points from a marriage."""
        pass

    def get_trump_suit(self) -> Suit:
        """Get the suit of the trump"""
        return self.__game_state.trump_suit

    def get_trump_card(self) -> Optional[Card]:
        """Get the card which is at the bottom of the talon. Will be None if the talon is empty"""
        return self.__game_state.talon.trump_card()

    def get_talon_size(self) -> int:
        """How many cards are still on the talon?"""
        return len(self.__game_state.talon)

    def get_phase(self) -> GamePhase:
        """What is the pahse of the game? This returns a GamePhase object.
        You can check the phase by checking state.get_phase == GamePhase.ONE
        """
        return self.__game_state.game_phase()

    @abstractmethod
    def get_opponent_hand_in_phase_two(self) -> Hand:
        """If the game is in the second phase, you can get the cards in the hand of the opponent.
        If this gets called, but the second pahse has not started yet, this will throw en Exception
        """
        pass

    @abstractmethod
    def am_i_leader(self) -> bool:
        """Returns True if the bot is the leader of this trick, False if it is a follower."""
        pass

    @abstractmethod
    def get_won_cards(self) -> CardCollection:
        """Get a list of all cards this Bot has won until now."""
        pass

    @abstractmethod
    def get_opponent_won_cards(self) -> CardCollection:
        """Get the list of cards the opponent has won until now."""
        pass

    def __get_own_bot_state(self) -> BotState:
        """Get the internal state object of this bot. This should not be used by a bot."""
        bot: BotState
        if self.am_i_leader():
            bot = self.__game_state.leader
        else:
            bot = self.__game_state.follower
        return bot

    def __get_opponent_bot_state(self) -> BotState:
        """Get the internal state object of the other bot. This should not be used by a bot."""
        bot: BotState
        if self.am_i_leader():
            bot = self.__game_state.follower
        else:
            bot = self.__game_state.leader
        return bot

    def seen_cards(self) -> CardCollection:
        """Get a list of all cards your bot has seen until now"""
        bot = self.__get_own_bot_state()

        seen_cards: set[Card] = set()  # We make it a set to remove duplicates

        # in own hand
        seen_cards.update(bot.hand)

        # the trump card
        trump = self.get_trump_card()
        if trump:
            seen_cards.add(trump)

        # all cards which were played in Tricks (icludes marriages and Trump exchanges)

        seen_cards.update(self.__past_tricks_cards())

        return OrderedCardCollection(seen_cards)

    def __past_tricks_cards(self) -> set[Card]:
        past_cards: set[Card] = set()
        prev = self.__game_state.previous
        while prev:
            past_cards.update(prev.trick.cards)
            prev = prev.state.previous
        return past_cards

    def get_known_cards_of_opponent_hand(self) -> CardCollection:
        """Get all cards which are in the opponents hand, but known to your Bot. This includes cards earlier used in marriages, or a trump exchange.
        All cards in the second pahse of the game."""
        opponent_hand = self.__get_opponent_bot_state().hand
        if self.get_phase() == GamePhase.TWO:
            return opponent_hand
        # We only disclose cards which have been part of a move, i.e., an Exchange or a Marriage
        past_trick_cards = self.__past_tricks_cards()
        return OrderedCardCollection(filter(lambda c: c in past_trick_cards, opponent_hand))

    def get_state_in_phase_two(self) -> GameState:
        """
        In phase TWO of the game, all information is known, so you can get the complete state

        This removes the real bots from the GameState. If you want to continue the game, provide new Bots. See copy_with_other_bots in the GameState class.
        """

        if self.get_phase() == GamePhase.TWO:
            return self.__game_state.copy_with_other_bots(_DummyBot(), _DummyBot())
        else:
            raise AssertionError("You cannot get the state in phase one")

    def make_assumption(self, rand: Random) -> GameState:
        """
        Takes the current imperfect information state and makes a random guess as to the position of the unknown cards.
        This also takes into account cards seen earlier during marriages played by the opponent, as well as potential trump jack exchanges

        This removes the real bots from the GameState. If you want to continue the game, provide new Bots. See copy_with_other_bots in the GameState class.

        :returns: A perfect information state object.
        """
        full_state = self.__game_state.copy_with_other_bots(_DummyBot(), _DummyBot())
        if self.get_phase() == GamePhase.TWO:
            return full_state

        seen_cards = self.seen_cards()
        full_deck = self.__engine.deck_generator.get_initial_deck()

        opponent_hand = self.__get_opponent_bot_state().hand.copy()
        unseen_opponent_hand = list(filter(lambda card: card not in seen_cards, opponent_hand))

        talon = full_state.talon
        unseen_talon = list(filter(lambda card: card not in seen_cards, talon))

        unseen_cards = list(filter(lambda card: card not in seen_cards, full_deck))
        rand.shuffle(unseen_cards)

        assert len(unseen_talon) + len(unseen_opponent_hand) == len(unseen_cards), "Logical error. The number of unseen cards in the opponents hand and in the talon must be equal to the number of unseen cards"

        new_talon = []
        for card in talon:
            if card in unseen_talon:
                # take one of the random cards
                new_talon.append(unseen_cards.pop())
            else:
                new_talon.append(card)

        full_state.talon = Talon(new_talon)

        new_opponent_hand = []
        for card in opponent_hand:
            if card in unseen_opponent_hand:
                new_opponent_hand.append(unseen_cards.pop())
            else:
                new_opponent_hand.append(card)
        if self.am_i_leader():
            full_state.follower.hand = Hand(new_opponent_hand)
        else:
            full_state.leader.hand = Hand(new_opponent_hand)

        assert len(unseen_cards) == 0, "All cards must be consumed by wither the opponent hand or talon by now"

        return full_state


class _DummyBot(Bot):
    """A bit used by PlayerPerspective.make_assumption to replace the real bots. This bot cannot play and will throw an Exception for everything"""

    def get_move(self, state: 'PlayerPerspective', leader_move: Optional['Move']) -> 'Move':
        raise Exception("The GameState from make_assumption removes the real bots from the Game. If you want to continue the game, provide new Bots. See copy_with_other_bots in the GameState class.")

    def notify_game_end(self, won: bool, state: 'PlayerPerspective') -> None:
        raise Exception("The GameState from make_assumption removes the real bots from the Game. If you want to continue the game, provide new Bots. See copy_with_other_bots in the GameState class.")

    def notify_trump_exchange(self, move: 'Trump_Exchange') -> None:
        raise Exception("The GameState from make_assumption removes the real bots from the Game. If you want to continue the game, provide new Bots. See copy_with_other_bots in the GameState class.")


class LeaderPerspective(PlayerPerspective):

    def __init__(self, state: 'GameState', engine: 'GamePlayEngine') -> None:
        super().__init__(state, engine)
        self.__game_state = state
        self.__engine = engine

    def valid_moves(self) -> List[Move]:
        moves = self.__engine.move_validator.get_legal_leader_moves(self.__engine, self.__game_state)
        return list(moves)

    def get_hand(self) -> Hand:
        return self.__game_state.leader.hand.copy()

    def get_my_score(self) -> Score:
        return self.__game_state.leader.score

    def get_opponent_score(self) -> Score:
        return self.__game_state.follower.score

    def get_opponent_hand_in_phase_two(self) -> Hand:
        assert self.get_phase() == GamePhase.TWO
        return self.__game_state.follower.hand.copy()

    def am_i_leader(self) -> bool:
        return True

    def get_won_cards(self) -> CardCollection:
        return OrderedCardCollection(self.__game_state.leader.won_cards)

    def get_opponent_won_cards(self) -> CardCollection:
        return OrderedCardCollection(self.__game_state.follower.won_cards)

    def __repr__(self) -> str:
        return f"LeaderGameState(state={self.__game_state}, engine={self.__engine})"


class FollowerPerspective(PlayerPerspective):
    def __init__(self, state: 'GameState', engine: 'GamePlayEngine', partial_trick: Optional[Move]) -> None:
        super().__init__(state, engine)
        self.__game_state = state
        self.__engine = engine
        self.__partial_trick = partial_trick

    def valid_moves(self) -> List[Move]:
        assert self.__partial_trick, "There is no partial trick for this follower, so no valid moves."
        return list(self.__engine.move_validator.get_legal_follower_moves(self.__engine, self.__game_state, self.__partial_trick))

    def get_hand(self) -> Hand:
        return self.__game_state.follower.hand.copy()

    def get_my_score(self) -> Score:
        return self.__game_state.follower.score

    def get_opponent_score(self) -> Score:
        return self.__game_state.leader.score

    def get_opponent_hand_in_phase_two(self) -> Hand:
        assert self.get_phase() == GamePhase.TWO
        return self.__game_state.leader.hand.copy()

    def am_i_leader(self) -> bool:
        return False

    def get_won_cards(self) -> CardCollection:
        return OrderedCardCollection(self.__game_state.follower.won_cards)

    def get_opponent_won_cards(self) -> CardCollection:
        return OrderedCardCollection(self.__game_state.leader.won_cards)

    def __repr__(self) -> str:
        return f"FollowerGameState(state={self.__game_state}, engine={self.__engine}, "
        f"partial_trick={self.__partial_trick})"


class ExchangeFollowerPerspective(PlayerPerspective):
    """
    A special PlayerGameState only used for the history of a game in which a Trump Exchange happened.
    This state is does not allow any moves.
    """

    def __init__(self, state: 'GameState', engine: 'GamePlayEngine') -> None:
        super().__init__(state, engine)

    def valid_moves(self) -> List[Move]:
        """
        Get a list of all valid moves the bot can play at this point in the game.

        Design note: this could also return an Iterable[Move], but List[Move] was chosen to make the API easier to use.
        """
        return []

    def get_hand(self) -> Hand:
        return super().__game_state.follower.hand.copy()

    def get_my_score(self) -> Score:
        return super().__game_state.follower.score

    def get_opponent_score(self) -> Score:
        return super().__game_state.leader.score

    def get_trump_suit(self) -> Suit:
        return super().__game_state.trump_suit

    def get_opponent_hand_in_phase_two(self) -> Hand:
        assert self.get_phase() == GamePhase.TWO
        return super().__game_state.leader.hand.copy()

    def get_opponent_won_cards(self) -> CardCollection:
        return OrderedCardCollection(self.__game_state.leader.won_cards)

    def get_won_cards(self) -> CardCollection:
        return OrderedCardCollection(self.__game_state.follower.won_cards)

    def am_i_leader(self) -> bool:
        return False


class WinnerPerspective(LeaderPerspective):
    """The gamestate given to the winner of the game at the very end"""

    def __init__(self, state: 'GameState', engine: 'GamePlayEngine') -> None:
        self.__game_state = state
        self.__engine = engine
        super().__init__(state, engine)

    def valid_moves(self) -> List[Move]:
        raise Exception("Cannot request valid moves from the final PlayerGameState because the game is over")

    def __repr__(self) -> str:
        return f"WinnerGameState(state={self.__game_state}, engine={self.__engine})"


class LoserPerspective(FollowerPerspective):
    """The gamestate given to the loser of the game at the very end"""

    def __init__(self, state: 'GameState', engine: 'GamePlayEngine') -> None:
        self.__game_state = state
        self.__engine = engine
        super().__init__(state, engine, None)

    def valid_moves(self) -> List[Move]:
        raise Exception("Cannot request valid moves from the final PlayerGameState because the game is over")

    def __repr__(self) -> str:
        return f"LoserGameState(state={self.__game_state}, engine={self.__engine})"


class DeckGenerator(ABC):
    @ abstractmethod
    def get_initial_deck(self) -> OrderedCardCollection:
        pass

    @ classmethod
    def shuffle_deck(self, deck: OrderedCardCollection, rng: Random) -> OrderedCardCollection:
        the_cards = list(deck.get_cards())
        rng.shuffle(the_cards)
        return OrderedCardCollection(the_cards)


class SchnapsenDeckGenerator(DeckGenerator):

    @ classmethod
    def get_initial_deck(self) -> OrderedCardCollection:
        deck = OrderedCardCollection()
        for suit in Suit:
            for rank in [Rank.JACK, Rank.QUEEN, Rank.KING, Rank.TEN, Rank.ACE]:
                deck._cards.append(Card.get_card(rank, suit))
        return deck


class HandGenerator(ABC):
    @ abstractmethod
    def generateHands(self, cards: OrderedCardCollection) -> Tuple[Hand, Hand, Talon]:
        pass


class SchnapsenHandGenerator(HandGenerator):
    @ classmethod
    def generateHands(self, cards: OrderedCardCollection) -> Tuple[Hand, Hand, Talon]:
        the_cards = list(cards.get_cards())
        hand1 = Hand([the_cards[i] for i in range(0, 10, 2)], max_size=5)
        hand2 = Hand([the_cards[i] for i in range(1, 11, 2)], max_size=5)
        rest = Talon(the_cards[10:])
        return (hand1, hand2, rest)


class TrickImplementer(ABC):
    @ abstractmethod
    def play_trick(self, game_engine: 'GamePlayEngine', game_state: GameState) -> GameState:
        pass

    @ abstractmethod
    def play_trick_with_fixed_leader_move(self, game_engine: 'GamePlayEngine', game_state: GameState,
                                          leader_move: Move) -> GameState:
        pass


class SchnapsenTrickImplementer(TrickImplementer):

    def play_trick(self, game_engine: 'GamePlayEngine', old_game_state: GameState) -> GameState:
        leader_move = self.get_leader_move(game_engine, old_game_state)
        return self.play_trick_with_fixed_leader_move(game_engine=game_engine, old_game_state=old_game_state, leader_move=leader_move)

    def play_trick_with_fixed_leader_move(self, game_engine: 'GamePlayEngine', old_game_state: GameState,
                                          leader_move: Move) -> GameState:
        if leader_move.is_trump_exchange():
            next_game_state = old_game_state.copy_for_next()
            exchange = cast(Trump_Exchange, leader_move)
            self.play_trump_exchange(next_game_state, exchange)
            # remember the previous state
            next_game_state.previous = Previous(old_game_state, ExchangeTrick(exchange), True)
            # The whole trick ends here.
            return next_game_state

        # We have a PartialTrick, ask the follower for its move
        partial_trick = cast(Union[Marriage, RegularMove], leader_move)
        follower_move = self.get_follower_move(game_engine, old_game_state, partial_trick)

        trick = RegularTrick(leader_move=partial_trick, follower_move=follower_move)
        return self._apply_regular_trick(game_engine=game_engine, old_game_state=old_game_state, trick=trick)

    def _apply_regular_trick(self, game_engine: 'GamePlayEngine', old_game_state: GameState, trick: RegularTrick) -> GameState:

        # apply the trick to the next_game_state
        # The next game state will be modified during this trick. We start from the previous state
        next_game_state = old_game_state.copy_for_next()

        if trick.leader_move.is_marriage():
            marriage_move: Marriage = cast(Marriage, trick.leader_move)
            self._play_marriage(game_engine, next_game_state, marriage_move=marriage_move)
            regular_leader_move: RegularMove = cast(Marriage, trick.leader_move).as_regular_move()
        else:
            regular_leader_move = cast(RegularMove, trick.leader_move)

        # # apply changes in the hand and talon
        next_game_state.leader.hand.remove(regular_leader_move.card)
        next_game_state.follower.hand.remove(trick.follower_move.card)

        # We set the leader for the next state based on what the scorer decides
        next_game_state.leader, next_game_state.follower, leader_remained_leader = game_engine.trick_scorer.score(trick, next_game_state.leader, next_game_state.follower, next_game_state.trump_suit)

        # important: the winner takes the first card of the talon, the loser the second one.
        # this also ensures that the loser of the last trick of the first phase gets the face up trump
        if not next_game_state.talon.is_empty():
            drawn = iter(next_game_state.talon.draw_cards(2))
            next_game_state.leader.hand.add(next(drawn))
            next_game_state.follower.hand.add(next(drawn))

        next_game_state.previous = Previous(old_game_state, trick=trick, leader_remained_leader=leader_remained_leader)

        return next_game_state

    def get_leader_move(self, game_engine: 'GamePlayEngine', old_game_state: 'GameState') -> Move:
        # ask first players move trough the requester
        leader_game_state = LeaderPerspective(old_game_state, game_engine)
        leader_move = game_engine.move_requester.get_move(old_game_state.leader, leader_game_state, None)
        if not game_engine.move_validator.is_legal_leader_move(game_engine, old_game_state, leader_move):
            raise Exception("Leader played an illegal move")

        return leader_move

    def play_trump_exchange(self, game_state: GameState, trump_exchange: Trump_Exchange) -> None:
        assert trump_exchange.jack.suit is game_state.trump_suit, \
            f"A trump exchange can only be done with a Jack of the same suit as the current trump. Got a {trump_exchange.jack} while the  Trump card is a {game_state.trump_suit}"
        # apply the changes in the gamestate
        game_state.leader.hand.remove(trump_exchange.jack)
        old_trump = game_state.talon.trump_exchange(trump_exchange.jack)
        game_state.leader.hand.add(old_trump)
        # We notify the other bot that an exchange happened
        game_state.follower.implementation.notify_trump_exchange(trump_exchange)

    def _play_marriage(self, game_engine: 'GamePlayEngine', game_state: GameState, marriage_move: Marriage) -> None:
        score = game_engine.trick_scorer.marriage(marriage_move, game_state)
        game_state.leader.score += score

    def get_follower_move(self, game_engine: 'GamePlayEngine', game_state: 'GameState', partial_trick: Move) -> RegularMove:
        follower_game_state = FollowerPerspective(game_state, game_engine, partial_trick)

        follower_move = game_engine.move_requester.get_move(game_state.follower, follower_game_state, partial_trick)
        if follower_move not in game_engine.move_validator.get_legal_follower_moves(game_engine, game_state, partial_trick):
            raise Exception("Follower played an illegal move")
        return cast(RegularMove, follower_move)


class MoveRequester:
    """An the logic of requesting a move from a bot.
    This logic also determines what happens in case the bot is to slow, throws an exception during operation, etc"""

    @ abstractmethod
    def get_move(self, bot: BotState, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        pass


class SimpleMoveRequester(MoveRequester):

    """The simplest just asks the move"""

    def get_move(self, bot: BotState, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        return bot.get_move(state, leader_move=leader_move)


class MoveValidator(ABC):
    @ abstractmethod
    def get_legal_leader_moves(self, game_engine: 'GamePlayEngine', game_state: GameState) -> Iterable[Move]:
        pass

    @ abstractmethod
    def get_legal_follower_moves(self, game_engine: 'GamePlayEngine', game_state: GameState, partial_trick: Move) -> Iterable[Move]:
        pass

    def is_legal_leader_move(self, game_engine: 'GamePlayEngine', game_state: GameState, move: Move) -> bool:
        return move in self.get_legal_leader_moves(game_engine, game_state)


class SchnapsenMoveValidator(MoveValidator):

    def get_legal_leader_moves(self, game_engine: 'GamePlayEngine', game_state: GameState) -> Iterable[Move]:
        # all cards in the hand can be played
        cards_in_hand = game_state.leader.hand
        valid_moves: List[Move] = [RegularMove(card) for card in cards_in_hand]
        # trump exchanges
        if not game_state.talon.is_empty():
            trump_jack = Card.get_card(Rank.JACK, game_state.trump_suit)
            if trump_jack in cards_in_hand:
                valid_moves.append(Trump_Exchange(trump_jack))
        # mariages
        for card in cards_in_hand.filter_rank(Rank.QUEEN):
            king_card = Card.get_card(Rank.KING, card.suit)
            if king_card in cards_in_hand:
                valid_moves.append(Marriage(card, king_card))
        return valid_moves

    def is_legal_leader_move(self, game_engine: 'GamePlayEngine', game_state: GameState, move: Move) -> bool:
        cards_in_hand = game_state.leader.hand
        if move.is_marriage():
            marriage_move = cast(Marriage, move)
            # we do not have to check whether they are the same suit because of the implementation of Marriage
            return marriage_move.queen_card in cards_in_hand and marriage_move.king_card in cards_in_hand
        if move.is_trump_exchange():
            if game_state.talon.is_empty():
                return False
            trump_move: Trump_Exchange = cast(Trump_Exchange, move)
            return trump_move.jack in cards_in_hand
        # it has to be a regular move
        regular_move = cast(RegularMove, move)
        return regular_move.card in cards_in_hand

    def get_legal_follower_moves(self, game_engine: 'GamePlayEngine', game_state: GameState, partial_trick: Move) -> Iterable[Move]:
        hand = game_state.follower.hand
        if partial_trick.is_marriage():
            leader_card = cast(Marriage, partial_trick).queen_card
        else:
            leader_card = cast(RegularMove, partial_trick).card
        if game_state.game_phase() is GamePhase.ONE:
            # no need to follow, any card in the hand is a legal move
            return RegularMove.from_cards(hand.get_cards())
        else:
            # information from https://www.pagat.com/marriage/schnaps.html
            # ## original formulation ##
            # if your opponent leads a non-trump:
            #     you must play a higher card of the same suit if you can;
            #     failing this you must play a lower card of the same suit;
            #     if you have no card of the suit that was led you must play a trump;
            #     if you have no trumps either you may play anything.
            # If your opponent leads a trump:
            #     you must play a higher trump if possible;
            #     if you have no higher trump you must play a lower trump;
            #     if you have no trumps at all you may play anything.
            # ## implemented version, realizing that the rules for trump are overlapping with the normal case ##
            # you must play a higher card of the same suit if you can
            # failing this, you must play a lower card of the same suit;
            # --new--> failing this, if the opponen did not play a trump, you must play a trump
            # failing this, you can play anything
            leader_card_score = game_engine.trick_scorer.rank_to_points(leader_card.rank)
            # you must play a higher card of the same suit if you can;
            same_suit_cards = hand.filter_suit(leader_card.suit)
            if same_suit_cards:
                higher_same_suit, lower_same_suit = [], []
                for card in same_suit_cards:
                    # TODO this is slightly ambigousm should this be >= ??
                    higher_same_suit.append(card) if game_engine.trick_scorer.rank_to_points(card.rank) > leader_card_score else lower_same_suit.append(card)
                if higher_same_suit:
                    return RegularMove.from_cards(higher_same_suit)
            # failing this, you must play a lower card of the same suit;
                elif lower_same_suit:
                    return RegularMove.from_cards(lower_same_suit)
                raise AssertionError("Somethign is wrong in the logic here. There should be cards, but they are neither placed in the low, nor higher list")
            # failing this, if the opponen did not play a trump, you must play a trump
            trump_cards = hand.filter_suit(game_state.trump_suit)
            if leader_card.suit != game_state.trump_suit and trump_cards:
                return RegularMove.from_cards(trump_cards)
            # failing this, you can play anything
            return RegularMove.from_cards(hand.get_cards())


class TrickScorer(ABC):
    @ abstractmethod
    def score(self, trick: RegularTrick, leader: BotState, follower: BotState, trump: Suit) -> Tuple[BotState, BotState, bool]:
        """
        Score the trick for the given leader and follower. The returned bots are copies and have the score of the trick applied.
        They are returned in order (new_leader, new_follower). If appropriate, also pending points have been applied.
        The boolean is True if the leading bot remained the same, i.e., the past leader remains the leader
        """
        pass

    @ abstractmethod
    def declare_winner(self, game_state: GameState) -> Optional[Tuple[BotState, int]]:
        """return a bot and the number of points if there is a winner of this game already"""
        pass

    @ abstractmethod
    def rank_to_points(self, rank: Rank) -> int:
        pass

    @ abstractmethod
    def marriage(self, move: Marriage, gamestate: GameState) -> 'Score':
        pass


class SchnapsenTrickScorer(TrickScorer):

    SCORES = {
        Rank.ACE: 11,
        Rank.TEN: 10,
        Rank.KING: 4,
        Rank.QUEEN: 3,
        Rank.JACK: 2,
    }

    def rank_to_points(self, rank: Rank) -> int:
        return SchnapsenTrickScorer.SCORES[rank]

    def marriage(self, move: Marriage, gamestate: GameState) -> 'Score':
        if move.suit is gamestate.trump_suit:
            # royal marriage
            return Score(pending_points=40)
        else:
            # any other marriage
            return Score(pending_points=20)

    def score(self, trick: RegularTrick, leader: BotState, follower: BotState, trump: Suit) -> Tuple[BotState, BotState, bool]:

        if trick.leader_move.is_marriage():
            regular_leader_move: RegularMove = cast(Marriage, trick.leader_move).as_regular_move()
        else:
            regular_leader_move = cast(RegularMove, trick.leader_move)

        leader_card = regular_leader_move.card
        follower_card = trick.follower_move.card
        assert leader_card != follower_card
        leader_card_points = self.rank_to_points(leader_card.rank)
        follower_card_points = self.rank_to_points(follower_card.rank)

        if leader_card.suit is follower_card.suit:
            # same suit, either trump or not
            if leader_card_points > follower_card_points:
                leader_wins = True
            else:
                leader_wins = False
        elif leader_card.suit is trump:
            # the follower suit cannot be trumps as per the previous condition
            leader_wins = True
        elif follower_card.suit is trump:
            # the leader suit cannot be trumps because of the previous conditions
            leader_wins = False
        else:
            # the follower did not follow the suit of the leader and did not play trumps, hence the leader wins
            leader_wins = True
        winner, loser = (leader, follower) if leader_wins else (follower, leader)
        # record the win
        winner.won_cards.extend([leader_card, follower_card])
        # apply the points
        points_gained = leader_card_points + follower_card_points
        winner.score += Score(direct_points=points_gained)
        # add winner's total of direct and pending points as their new direct points
        winner.score = winner.score.redeem_pending_points()
        return winner, loser, leader_wins

    def declare_winner(self, game_state: GameState) -> Optional[Tuple[BotState, int]]:
        """
        Declaring a winner uses the logic from https://www.pagat.com/marriage/schnaps.html#marriages , but simplified, because we do not have closing of the Talon and no need to guess the scores.
        The following text adapted accordingly from that website.

        If a player has 66 or more points, she scores points toward game as follows:

            * one game point, if the opponent has made at least 33 points;
            * two game points, if the opponent has made fewer than 33 points, but has won at least one trick (opponent is said to be Schneider);
            * three game points, if the opponent has won no tricks (opponent is said to be Schwarz).

        If play continued to the very last trick with the talon exhausted, the player who takes the last trick wins the hand, scoring one game point, irrespective of the number of card points the players have taken.
        """
        if game_state.leader.score.direct_points >= 66:
            follower_score = game_state.follower.score.direct_points
            if follower_score == 0:
                return game_state.leader, 3
            elif follower_score >= 33:
                return game_state.leader, 1
            else:
                # second case in explaination above, 0 < score < 33
                assert follower_score < 66
                return game_state.leader, 2
        elif game_state.follower.score.direct_points >= 66:
            raise AssertionError("Would declare the follower winner, but this should never happen in the current implementation")
        elif game_state.are_all_cards_played():
            return game_state.leader, 1
        else:
            return None


@ dataclass
class GamePlayEngine:
    deck_generator: DeckGenerator
    hand_generator: HandGenerator
    trick_implementer: TrickImplementer
    move_requester: MoveRequester
    move_validator: MoveValidator
    trick_scorer: TrickScorer

    def play_game(self, bot1: Bot, bot2: Bot, rng: Random) -> Tuple[Bot, int, Score]:
        cards = self.deck_generator.get_initial_deck()
        shuffled = self.deck_generator.shuffle_deck(cards, rng)
        hand1, hand2, talon = self.hand_generator.generateHands(shuffled)

        leader_state = BotState(implementation=bot1, hand=hand1)
        follower_state = BotState(implementation=bot2, hand=hand2)

        game_state = GameState(
            leader=leader_state,
            follower=follower_state,
            talon=talon,
            previous=None
        )
        winner, points, score = self.play_game_from_state(game_state=game_state, leader_move=None)
        return winner, points, score

    def play_game_from_state_with_new_bots(self, game_state: GameState, new_leader: Bot, new_follower: Bot, leader_move: Optional[Move]) -> Tuple[Bot, int, Score]:

        game_state_copy = game_state.copy_with_other_bots(new_leader=new_leader, new_follower=new_follower)
        return self.play_game_from_state(game_state_copy, leader_move=leader_move)

    def play_game_from_state(self, game_state: GameState, leader_move: Optional[Move]) -> Tuple[Bot, int, Score]:

        winner: Optional[BotState] = None
        points: int = -1
        while not winner:
            if leader_move is not None:
                # we continues from a game where the leading bot already did a move, we immitate that
                game_state = self.trick_implementer.play_trick_with_fixed_leader_move(self, game_state=game_state, leader_move=leader_move)
                leader_move = None
            else:
                game_state = self.trick_implementer.play_trick(self, game_state)
            winner, points = self.trick_scorer.declare_winner(game_state) or (None, -1)

        winner_state = WinnerPerspective(game_state, self)
        winner.implementation.notify_game_end(won=True, state=winner_state)

        loser_state = LoserPerspective(game_state, self)
        game_state.follower.implementation.notify_game_end(False, state=loser_state)

        return winner.implementation, points, winner.score

    def __repr__(self) -> str:
        return f"GamePlayEngine(deck_generator={self.deck_generator}, "\
               f"hand_generator={self.hand_generator}, "\
               f"trick_implementer={self.trick_implementer}, "\
               f"move_requester={self.move_requester}, "\
               f"move_validator={self.move_validator}, "\
               f"trick_scorer={self.trick_scorer})"


class SchnapsenGamePlayEngine(GamePlayEngine):
    def __init__(self) -> None:
        super().__init__(
            deck_generator=SchnapsenDeckGenerator(),
            hand_generator=SchnapsenHandGenerator(),
            trick_implementer=SchnapsenTrickImplementer(),
            move_requester=SimpleMoveRequester(),
            move_validator=SchnapsenMoveValidator(),
            trick_scorer=SchnapsenTrickScorer()
        )

    def __repr__(self) -> str:
        return super().__repr__()


# engine = GamePlayEngine(startingDeck=MyDeck(), hand_generator = HandGenetation, play_trick = MyPlayTrick(), move_requester=Move_Requester, move_validator = MoveValidator(), scorer = ScoreThing() ),


# engine.play_game(bot1, bot 2)
