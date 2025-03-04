"""
Card module for Texas Hold'em Poker.
Implements Card, Suit, Rank, and Deck classes.
"""
from __future__ import annotations
from enum import Enum, auto
import random
from typing import List, Optional, Set


class Suit(Enum):
    """Card suits with unicode symbols."""
    CLUBS = "♣"
    DIAMONDS = "♦"
    HEARTS = "♥"
    SPADES = "♠"

    @property
    def color(self) -> str:
        """Return the color of the suit: red for hearts/diamonds, black for clubs/spades."""
        return "red" if self in (Suit.HEARTS, Suit.DIAMONDS) else "black"


class Rank(Enum):
    """Card ranks with values."""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def symbol(self) -> str:
        """Return the display symbol for the rank."""
        if self.value <= 10:
            return str(self.value)
        symbols = {
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
            Rank.ACE: "A"
        }
        return symbols[self]


class Card:
    """
    Represents a playing card with a rank and suit.
    """
    def __init__(self, rank: Rank, suit: Suit):
        """Initialize a new card with the given rank and suit."""
        self.rank = rank
        self.suit = suit

    def __repr__(self) -> str:
        """String representation of the card."""
        return f"{self.rank.symbol}{self.suit.value}"

    def __eq__(self, other: object) -> bool:
        """Compare two cards for equality."""
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        """Hash value for the card."""
        return hash((self.rank, self.suit))

    @property
    def value(self) -> int:
        """Numeric value of the card."""
        return self.rank.value


class Deck:
    """
    Represents a deck of 52 playing cards.
    """
    def __init__(self):
        """Initialize a new ordered deck of cards."""
        self.cards: List[Card] = []
        self.reset()

    def reset(self) -> None:
        """Reset the deck to its initial state."""
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]

    def shuffle(self) -> None:
        """Shuffle the cards in the deck."""
        random.shuffle(self.cards)

    def deal(self) -> Optional[Card]:
        """
        Deal a card from the top of the deck.
        Returns None if the deck is empty.
        """
        if not self.cards:
            return None
        return self.cards.pop(0)

    def deal_multiple(self, count: int) -> List[Card]:
        """
        Deal multiple cards from the deck.
        Returns fewer cards if the deck doesn't have enough.
        """
        cards = []
        for _ in range(min(count, len(self.cards))):
            card = self.deal()
            if card:  # This check is technically redundant given the range, but keeps mypy happy
                cards.append(card)
        return cards

    @property
    def remaining(self) -> int:
        """Number of cards remaining in the deck."""
        return len(self.cards)

    def burn(self) -> Optional[Card]:
        """
        Burn a card (remove it from play).
        Returns the burned card or None if the deck is empty.
        """
        return self.deal()


def create_deck() -> Deck:
    """Create a new shuffled deck."""
    deck = Deck()
    deck.shuffle()
    return deck