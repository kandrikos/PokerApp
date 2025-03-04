"""
Table module for Texas Hold'em Poker.
Implements Table class for managing players and seats.
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Set
import random

from core.player import Player, PlayerStatus


class Table:
    """
    Represents a poker table with seats and players.
    """
    def __init__(self, table_id: str, name: str, max_seats: int = 9):
        """
        Initialize a new poker table.
        
        Args:
            table_id: Unique identifier for the table
            name: Display name for the table
            max_seats: Maximum number of seats at the table (default 9)
        """
        self.id = table_id
        self.name = name
        self.max_seats = max_seats
        self.seats: List[Optional[Player]] = [None] * max_seats
        self.dealer_position = -1  # Position of the dealer button
        self.active_players: List[Player] = []  # Players currently in the hand
        
    def __repr__(self) -> str:
        """String representation of the table."""
        occupied = sum(1 for seat in self.seats if seat is not None)
        return f"Table({self.name}, {occupied}/{self.max_seats} players)"
    
    def add_player(self, player: Player, position: int = -1) -> bool:
        """
        Add a player to the table at the specified position.
        If position is -1, the first available seat is used.
        
        Returns:
            True if the player was added, False otherwise
        """
        # If no position specified, find the first available seat
        if position == -1:
            for i, seat in enumerate(self.seats):
                if seat is None:
                    position = i
                    break
            else:
                return False  # No seats available
        
        # Check if the position is valid and available
        if position < 0 or position >= self.max_seats or self.seats[position] is not None:
            return False
        
        # Add the player to the table
        self.seats[position] = player
        player.position = position
        return True
    
    def remove_player(self, player: Player) -> bool:
        """
        Remove a player from the table.
        
        Returns:
            True if the player was removed, False if not found
        """
        position = player.position
        if position >= 0 and position < self.max_seats and self.seats[position] == player:
            self.seats[position] = None
            player.position = -1
            return True
        return False
    
    def get_player_at_position(self, position: int) -> Optional[Player]:
        """Get the player at the specified position."""
        if 0 <= position < self.max_seats:
            return self.seats[position]
        return None
    
    def get_player_positions(self) -> Dict[str, int]:
        """
        Get a mapping of player IDs to their positions.
        
        Returns:
            Dictionary mapping player IDs to seat positions
        """
        result = {}
        for i, player in enumerate(self.seats):
            if player is not None:
                result[player.id] = i
        return result
    
    def get_empty_seats(self) -> List[int]:
        """Get a list of empty seat positions."""
        return [i for i, seat in enumerate(self.seats) if seat is None]
    
    def is_full(self) -> bool:
        """Check if the table is full."""
        return None not in self.seats
    
    def is_empty(self) -> bool:
        """Check if the table is empty."""
        return all(seat is None for seat in self.seats)
    
    def player_count(self) -> int:
        """Get the number of players at the table."""
        return sum(1 for seat in self.seats if seat is not None)
    
    def active_player_count(self) -> int:
        """Get the number of active players at the table."""
        return sum(1 for seat in self.seats if seat is not None and 
                  seat.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN))
    
    def advance_dealer_button(self) -> int:
        """
        Advance the dealer button to the next player who has chips.
        
        Returns:
            The new dealer position
        """
        # Get list of active positions (seats with non-eliminated players)
        active_positions = [i for i, seat in enumerate(self.seats) if seat is not None and 
                         seat.status != PlayerStatus.ELIMINATED and seat.chips > 0]
        
        if not active_positions:
            self.dealer_position = -1
            return -1
        
        # If dealer position is invalid, or current dealer is eliminated/has no chips
        if (self.dealer_position == -1 or 
            self.dealer_position >= len(self.seats) or 
            self.seats[self.dealer_position] is None or
            self.seats[self.dealer_position].status == PlayerStatus.ELIMINATED or
            self.seats[self.dealer_position].chips == 0):
            
            # If we have a valid dealer position, find the next seat after it
            if 0 <= self.dealer_position < len(self.seats):
                # Find positions after the current dealer
                next_positions = [pos for pos in active_positions if pos > self.dealer_position]
                if next_positions:
                    # Move to next active position after current dealer
                    self.dealer_position = next_positions[0]
                    return self.dealer_position
            
            # Otherwise, move to the first active position
            self.dealer_position = active_positions[0]
            return self.dealer_position
        
        # Find the current dealer's index in our active positions list
        try:
            current_idx = active_positions.index(self.dealer_position)
            # Move to the next active position (wrap around if needed)
            next_idx = (current_idx + 1) % len(active_positions)
            self.dealer_position = active_positions[next_idx]
            return self.dealer_position
        except ValueError:
            # Current dealer position not in active positions
            # Find positions after the current dealer
            next_positions = [pos for pos in active_positions if pos > self.dealer_position]
            if next_positions:
                # Move to next active position after current dealer
                self.dealer_position = next_positions[0]
            else:
                # Wrap around to first active position
                self.dealer_position = active_positions[0]
            return self.dealer_position
    
    def get_blinds_positions(self) -> Tuple[int, int]:
        """
        Get the positions of the small blind and big blind.
        Skip eliminated players or players with zero chips.
        
        Returns:
            Tuple of (small_blind_position, big_blind_position)
        """
        if self.dealer_position == -1:
            return -1, -1
        
        # Get list of active players with chips
        active_players = [i for i, seat in enumerate(self.seats) if seat is not None and 
                        seat.status != PlayerStatus.ELIMINATED and seat.chips > 0]
        
        if len(active_players) < 2:
            return -1, -1
            
        # Find dealer index in active players list
        try:
            dealer_idx = active_players.index(self.dealer_position)
        except ValueError:
            # Dealer not in active players (shouldn't happen but just in case)
            dealer_idx = 0
        
        # For heads-up play (2 players), the dealer posts the small blind
        if len(active_players) == 2:
            sb_idx = dealer_idx
            bb_idx = (dealer_idx + 1) % 2
            
            return active_players[sb_idx], active_players[bb_idx]
        
        # For 3+ players, small blind is to the left of the dealer
        sb_idx = (dealer_idx + 1) % len(active_players)
        bb_idx = (dealer_idx + 2) % len(active_players)
        
        return active_players[sb_idx], active_players[bb_idx]
    
    def get_active_players(self) -> List[Player]:
        """
        Get a list of active players (not folded or eliminated) in seat order.
        
        Returns:
            List of active players starting from the seat after the dealer
        """
        active = []
        if self.dealer_position == -1:
            # No dealer yet, just return players in seat order
            for seat in self.seats:
                if seat is not None and seat.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN):
                    active.append(seat)
        else:
            # Start from the seat after the dealer
            start_pos = (self.dealer_position + 1) % self.max_seats
            current_pos = start_pos
            
            # Go around the table once
            while True:
                seat = self.seats[current_pos]
                if seat is not None and seat.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN):
                    active.append(seat)
                
                current_pos = (current_pos + 1) % self.max_seats
                if current_pos == start_pos:
                    break
        
        return active
    
    def update_active_players(self) -> None:
        """Update the list of active players."""
        self.active_players = self.get_active_players()
    
    def get_next_to_act(self, after_position: int = -1) -> Optional[Player]:
        """
        Get the next player to act after the specified position.
        If after_position is -1, start from the beginning.
        
        Returns:
            The next player to act, or None if no players can act
        """
        if not self.active_players:
            self.update_active_players()
        
        if not self.active_players:
            return None
        
        # Find players who can still act
        can_act = [p for p in self.active_players if p.status == PlayerStatus.ACTIVE and not p.has_acted]
        if not can_act:
            return None
        
        if after_position == -1:
            return can_act[0]
        
        # Find the next player after the specified position
        start_idx = 0
        for i, player in enumerate(self.active_players):
            if player.position > after_position:
                start_idx = i
                break
        
        # Check from start_idx to the end
        for player in self.active_players[start_idx:]:
            if player.status == PlayerStatus.ACTIVE and not player.has_acted:
                return player
        
        # Check from the beginning to start_idx
        for player in self.active_players[:start_idx]:
            if player.status == PlayerStatus.ACTIVE and not player.has_acted:
                return player
        
        return None
    
    def _next_occupied_seat(self, from_position: int) -> int:
        """
        Find the next occupied seat after the specified position.
        
        Args:
            from_position: Starting position
            
        Returns:
            The position of the next occupied seat
        """
        current_pos = (from_position + 1) % self.max_seats
        while current_pos != from_position:
            if self.seats[current_pos] is not None:
                return current_pos
            current_pos = (current_pos + 1) % self.max_seats
        
        # If we've gone full circle and found nothing, return the starting position
        return from_position
    
    def reset_player_states(self) -> None:
        """Reset the state of all players for a new hand."""
        for player in self.seats:
            if player is not None:
                player.reset_for_new_hand()