"""
Player module for Texas Hold'em Poker.
Implements Player class and related functionality.
"""
from __future__ import annotations
from enum import Enum, auto
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import uuid

from core.card import Card
from core.hand import Hand


class PlayerStatus(Enum):
    """Represents the current status of a player in a game."""
    ACTIVE = auto()      # Player is in the game and has not folded
    FOLDED = auto()      # Player has folded
    ALL_IN = auto()      # Player is all-in
    SITTING_OUT = auto() # Player is sitting out
    ELIMINATED = auto()  # Player is eliminated from the tournament


class Player:
    """
    Represents a player in the poker game.
    """
    def __init__(self, player_id: str = None, name: str = "Player", 
                 chips: int = 0, avatar: str = None):
        """
        Initialize a new player.
        
        Args:
            player_id: Unique identifier for the player (auto-generated if None)
            name: Display name for the player
            chips: Starting chip count
            avatar: Path or URL to player's avatar image
        """
        self.id = player_id or str(uuid.uuid4())
        self.name = name
        self.chips = chips
        self.avatar = avatar
        self.hand = Hand()
        self.status = PlayerStatus.SITTING_OUT
        self.current_bet = 0  # Amount bet in the current round
        self.total_bet = 0    # Total amount bet in the current hand
        self.position = -1    # Seat position at the table
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False
        self.has_acted = False  # Whether player has acted in the current betting round
        self.statistics: Dict[str, Any] = {
            "hands_played": 0,
            "hands_won": 0,
            "best_hand": None,
            "total_winnings": 0,
            "biggest_pot": 0
        }

    def __repr__(self) -> str:
        """String representation of the player."""
        return f"Player({self.name}, {self.chips} chips, {self.status.name})"

    def receive_card(self, card: Card) -> None:
        """Add a card to the player's hand."""
        self.hand.add_card(card)

    def clear_hand(self) -> None:
        """Clear the player's hand."""
        self.hand.clear()

    def place_bet(self, amount: int) -> int:
        """
        Place a bet of the given amount.
        
        Returns:
            The actual amount bet (may be less if player doesn't have enough chips)
        """
        # Ensure bet doesn't exceed available chips
        actual_amount = min(amount, self.chips)
        self.chips -= actual_amount
        self.current_bet += actual_amount
        self.total_bet += actual_amount
        
        # Check if player is all-in
        if self.chips == 0 and actual_amount > 0:
            self.status = PlayerStatus.ALL_IN
            
        return actual_amount

    def fold(self) -> None:
        """Fold the current hand."""
        if self.status == PlayerStatus.ACTIVE:
            self.status = PlayerStatus.FOLDED

    def sit_in(self) -> None:
        """Sit into the game."""
        if self.status in (PlayerStatus.SITTING_OUT, PlayerStatus.ELIMINATED) and self.chips > 0:
            self.status = PlayerStatus.ACTIVE

    def sit_out(self) -> None:
        """Sit out of the game."""
        if self.status not in (PlayerStatus.ELIMINATED, PlayerStatus.SITTING_OUT):
            self.status = PlayerStatus.SITTING_OUT

    def add_chips(self, amount: int) -> None:
        """Add chips to the player's stack."""
        self.chips += amount

    def reset_for_new_hand(self) -> None:
        """Reset player state for a new hand."""
        self.clear_hand()
        if self.status != PlayerStatus.ELIMINATED and self.chips > 0:
            self.status = PlayerStatus.ACTIVE
        self.current_bet = 0
        self.total_bet = 0
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False
        self.has_acted = False

    def reset_for_new_betting_round(self) -> None:
        """Reset player state for a new betting round."""
        self.current_bet = 0
        self.has_acted = False

    def can_act(self) -> bool:
        """Check if the player can act in the current round."""
        return (self.status == PlayerStatus.ACTIVE and 
                not self.has_acted and 
                self.chips > 0)

    def update_statistics(self, won: bool, amount: int, hand_description: Optional[str] = None) -> None:
        """Update player statistics after a hand."""
        self.statistics["hands_played"] += 1
        
        if won:
            self.statistics["hands_won"] += 1
            self.statistics["total_winnings"] += amount
            
            if amount > self.statistics["biggest_pot"]:
                self.statistics["biggest_pot"] = amount
                
        if hand_description and (self.statistics["best_hand"] is None or 
                               self._hand_rank(hand_description) > self._hand_rank(self.statistics["best_hand"])):
            self.statistics["best_hand"] = hand_description

    @staticmethod
    def _hand_rank(hand_description: str) -> int:
        """Helper method to rank hand descriptions for statistics."""
        rankings = {
            "High Card": 1,
            "Pair": 2,
            "Two Pair": 3,
            "Three of a Kind": 4,
            "Straight": 5,
            "Flush": 6,
            "Full House": 7,
            "Four of a Kind": 8,
            "Straight Flush": 9,
            "Royal Flush": 10
        }
        
        for rank_name, rank_value in rankings.items():
            if hand_description.startswith(rank_name):
                return rank_value
                
        return 0  # Unknown hand