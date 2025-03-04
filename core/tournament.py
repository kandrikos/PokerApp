"""
Tournament module for Texas Hold'em Poker.
Implements tournament structure and management.
"""
from __future__ import annotations
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple, Set, Any
import uuid
import logging
import time
from dataclasses import dataclass, field

from core.player import Player, PlayerStatus
from core.table import Table
from core.game import Game, GameStatus, GameConfig


class TournamentStatus(Enum):
    """Status of a poker tournament."""
    REGISTERING = auto()  # Registration is open
    STARTING = auto()     # Tournament is about to start
    RUNNING = auto()      # Tournament is in progress
    PAUSED = auto()       # Tournament is paused
    FINISHED = auto()     # Tournament is complete


@dataclass
class BlindLevel:
    """Defines a blind level in a tournament."""
    level: int
    small_blind: int
    big_blind: int
    ante: int = 0
    duration_minutes: int = 20


@dataclass
class TournamentConfig:
    """Configuration for a tournament."""
    name: str = "Tournament"
    buy_in: int = 1000
    starting_chips: int = 1000
    players_per_table: int = 9
    min_players: int = 2
    max_players: int = 100
    blind_levels: List[BlindLevel] = field(default_factory=list)
    payouts_percentage: List[float] = field(default_factory=list)
    allow_rebuys: bool = False
    allow_addons: bool = False
    rebuy_amount: int = 0
    addon_amount: int = 0


class Tournament:
    """
    Manages a poker tournament with multiple tables.
    """
    def __init__(self, tournament_id: str = None, config: TournamentConfig = None):
        """
        Initialize a new tournament.
        
        Args:
            tournament_id: Unique identifier for the tournament (auto-generated if None)
            config: Tournament configuration
        """
        self.id = tournament_id or str(uuid.uuid4())
        self.config = config or self._create_default_config()
        
        self.tables: List[Table] = []
        self.games: Dict[str, Game] = {}
        self.players: Dict[str, Player] = {}
        self.eliminated_players: List[Player] = []
        self.current_level = 0
        self.start_time: Optional[float] = None
        self.level_start_time: Optional[float] = None
        self.status = TournamentStatus.REGISTERING
        
        self.logger = logging.getLogger(f"poker.tournament.{self.id}")
    
    @staticmethod
    def _create_default_config() -> TournamentConfig:
        """Create a default tournament configuration."""
        blind_levels = [
            BlindLevel(1, 5, 10, 0, 20),
            BlindLevel(2, 10, 20, 0, 20),
            BlindLevel(3, 15, 30, 0, 20),
            BlindLevel(4, 20, 40, 5, 20),
            BlindLevel(5, 25, 50, 5, 20),
            BlindLevel(6, 50, 100, 10, 20),
            BlindLevel(7, 75, 150, 15, 20),
            BlindLevel(8, 100, 200, 25, 20),
            BlindLevel(9, 150, 300, 25, 20),
            BlindLevel(10, 200, 400, 50, 20),
            BlindLevel(11, 300, 600, 75, 15),
            BlindLevel(12, 400, 800, 100, 15),
            BlindLevel(13, 500, 1000, 125, 15),
            BlindLevel(14, 700, 1400, 150, 15),
            BlindLevel(15, 1000, 2000, 200, 15),
            BlindLevel(16, 1500, 3000, 300, 15),
            BlindLevel(17, 2000, 4000, 500, 15),
            BlindLevel(18, 3000, 6000, 1000, 15),
            BlindLevel(19, 5000, 10000, 1000, 15),
            BlindLevel(20, 7500, 15000, 2000, 15)
        ]
        
        # Standard payout percentages (adjust based on tournament size)
        payouts = [
            50.0,  # 1st place: 50%
            30.0,  # 2nd place: 30%
            20.0   # 3rd place: 20%
        ]
        
        return TournamentConfig(
            name="Default Tournament",
            buy_in=1000,
            starting_chips=1000,
            blind_levels=blind_levels,
            payouts_percentage=payouts
        )
    
    def register_player(self, player: Player) -> bool:
        """
        Register a player for the tournament.
        
        Args:
            player: Player to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        if self.status != TournamentStatus.REGISTERING:
            self.logger.warning(f"Cannot register player {player.name}: tournament is not in REGISTERING state")
            return False
        
        if len(self.players) >= self.config.max_players:
            self.logger.warning(f"Cannot register player {player.name}: tournament is full")
            return False
        
        if player.id in self.players:
            self.logger.warning(f"Player {player.name} is already registered")
            return False
        
        # Set up player for tournament
        player.chips = self.config.starting_chips
        player.status = PlayerStatus.SITTING_OUT
        self.players[player.id] = player
        
        self.logger.info(f"Player {player.name} registered for tournament")
        return True
    
    def unregister_player(self, player_id: str) -> bool:
        """
        Unregister a player from the tournament.
        
        Args:
            player_id: ID of the player to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if self.status != TournamentStatus.REGISTERING:
            self.logger.warning("Cannot unregister player: tournament is not in REGISTERING state")
            return False
        
        if player_id not in self.players:
            self.logger.warning(f"Player {player_id} is not registered")
            return False
        
        player = self.players.pop(player_id)
        self.logger.info(f"Player {player.name} unregistered from tournament")
        return True
    
    def start_tournament(self) -> bool:
        """
        Start the tournament.
        
        Returns:
            True if the tournament started successfully, False otherwise
        """
        if self.status != TournamentStatus.REGISTERING:
            self.logger.warning("Cannot start tournament: tournament is not in REGISTERING state")
            return False
        
        if len(self.players) < self.config.min_players:
            self.logger.warning(f"Cannot start tournament: need at least {self.config.min_players} players")
            return False
        
        self.status = TournamentStatus.STARTING
        self.start_time = time.time()
        self.level_start_time = self.start_time
        self.current_level = 0
        
        # Create tables and assign players
        self._create_tables()
        self._assign_players_to_tables()
        
        # Start the tournament
        self.status = TournamentStatus.RUNNING
        self._start_all_tables()
        
        self.logger.info(f"Tournament started with {len(self.players)} players at {self.level_start_time}")
        return True
    
    def _create_tables(self) -> None:
        """Create the necessary tables for the tournament."""
        # Calculate number of tables needed
        num_players = len(self.players)
        players_per_table = self.config.players_per_table
        num_tables = (num_players + players_per_table - 1) // players_per_table
        
        self.logger.info(f"Creating {num_tables} tables for {num_players} players")
        
        # Create tables
        self.tables = []
        for i in range(num_tables):
            table_id = f"{self.id}_table_{i+1}"
            table_name = f"Table {i+1}"
            table = Table(table_id, table_name, players_per_table)
            self.tables.append(table)
    
    def _assign_players_to_tables(self) -> None:
        """Assign players to tables in a balanced way."""
        player_list = list(self.players.values())
        num_tables = len(self.tables)
        
        if num_tables == 0:
            self.logger.warning("No tables available for player assignment")
            return
        
        # Shuffle players for random seating
        import random
        random.shuffle(player_list)
        
        # Calculate ideal distribution
        players_per_table = len(player_list) // num_tables
        extra_players = len(player_list) % num_tables
        
        # Assign players to tables
        player_index = 0
        for table_index, table in enumerate(self.tables):
            # Determine how many players should be at this table
            table_size = players_per_table + (1 if table_index < extra_players else 0)
            
            # Add players to the table
            for _ in range(table_size):
                if player_index < len(player_list):
                    player = player_list[player_index]
                    table.add_player(player)
                    player_index += 1
            
            self.logger.info(f"Table {table.name} has {table_size} players")
    
    def _start_all_tables(self) -> None:
        """Start games at all tables."""
        current_blinds = self._get_current_blinds()
        
        for table in self.tables:
            if table.player_count() < 2:
                self.logger.warning(f"Cannot start game at {table.name}: not enough players")
                continue
            
            # Create game config with current blind levels
            game_config = GameConfig(
                small_blind=current_blinds.small_blind,
                big_blind=current_blinds.big_blind,
                ante=current_blinds.ante,
                min_players=2,
                max_players=table.max_seats,
                starting_chips=self.config.starting_chips
            )
            
            # Create and start the game
            game = Game(f"{table.id}_game", table, game_config)
            self.games[table.id] = game
            game.start_hand()
            
            self.logger.info(f"Started game at {table.name}")
    
    def advance_level(self) -> bool:
        """
        Advance to the next blind level.
        
        Returns:
            True if successful, False if no more levels
        """
        if self.status != TournamentStatus.RUNNING:
            self.logger.warning("Cannot advance level: tournament is not running")
            return False
        
        if self.current_level >= len(self.config.blind_levels) - 1:
            self.logger.warning("Cannot advance level: already at maximum level")
            return False
        
        self.current_level += 1
        self.level_start_time = time.time()
        
        # Update blind levels for all active games
        current_blinds = self._get_current_blinds()
        for game in self.games.values():
            game.config.small_blind = current_blinds.small_blind
            game.config.big_blind = current_blinds.big_blind
            game.config.ante = current_blinds.ante
        
        self.logger.info(f"Advanced to blind level {self.current_level+1}: "
                        f"SB {current_blinds.small_blind}, BB {current_blinds.big_blind}, "
                        f"Ante {current_blinds.ante}")
        return True
    
    def _get_current_blinds(self) -> BlindLevel:
        """Get the current blind level."""
        if self.current_level < len(self.config.blind_levels):
            return self.config.blind_levels[self.current_level]
        else:
            # Return the highest level if beyond the defined levels
            return self.config.blind_levels[-1]
    
    def eliminate_player(self, player_id: str) -> bool:
        """
        Eliminate a player from the tournament.
        
        Args:
            player_id: ID of the player to eliminate
            
        Returns:
            True if elimination was successful, False otherwise
        """
        if player_id not in self.players:
            self.logger.warning(f"Cannot eliminate player {player_id}: not found in tournament")
            return False
        
        player = self.players[player_id]
        player.status = PlayerStatus.ELIMINATED
        
        # Find the player's table
        for table in self.tables:
            for i, seat in enumerate(table.seats):
                if seat is not None and seat.id == player_id:
                    # Remove player from table
                    table.seats[i] = None
                    break
        
        # Add to eliminated players list
        self.eliminated_players.append(player)
        
        # Check if tournament is finished
        remaining_players = sum(1 for p in self.players.values() if p.status != PlayerStatus.ELIMINATED)
        if remaining_players <= 1:
            self._finish_tournament()
        else:
            # Check if tables need to be balanced
            self._balance_tables()
        
        self.logger.info(f"Player {player.name} eliminated from tournament")
        return True
    
    def _balance_tables(self) -> None:
        """Balance players across tables if needed."""
        # Count active players at each table
        table_counts = [(table, sum(1 for seat in table.seats if seat is not None and 
                                  seat.status != PlayerStatus.ELIMINATED))
                        for table in self.tables]
        
        # Check if any tables need to be removed
        active_tables = [t for t, count in table_counts if count > 0]
        if len(active_tables) < len(self.tables):
            self.logger.info(f"Reducing from {len(self.tables)} to {len(active_tables)} tables")
            self.tables = active_tables
            table_counts = [(table, count) for table, count in table_counts if count > 0]
        
        if len(table_counts) <= 1:
            # Only one table left, no balancing needed
            return
        
        # Check if tables are imbalanced
        min_count = min(count for _, count in table_counts)
        max_count = max(count for _, count in table_counts)
        
        if max_count - min_count <= 1:
            # Tables are balanced (difference of at most 1 player)
            return
        
        self.logger.info(f"Balancing tables: min={min_count}, max={max_count} players")
        
        # Sort tables by player count (descending)
        table_counts.sort(key=lambda x: x[1], reverse=True)
        
        # Move players from larger tables to smaller ones
        while max_count - min_count > 1:
            # Find table with most players
            source_table, source_count = table_counts[0]
            
            # Find table with fewest players
            dest_table, dest_count = table_counts[-1]
            
            # Move a player
            self._move_player(source_table, dest_table)
            
            # Update counts
            table_counts[0] = (source_table, source_count - 1)
            table_counts[-1] = (dest_table, dest_count + 1)
            
            # Re-sort tables
            table_counts.sort(key=lambda x: x[1], reverse=True)
            
            # Update min/max
            min_count = table_counts[-1][1]
            max_count = table_counts[0][1]
    
    def _move_player(self, source_table: Table, dest_table: Table) -> None:
        """
        Move a player from one table to another.
        
        Args:
            source_table: Table to move player from
            dest_table: Table to move player to
        """
        # Find a player to move (use the one in the largest position)
        player_to_move = None
        for i in range(source_table.max_seats - 1, -1, -1):
            player = source_table.get_player_at_position(i)
            if player is not None and player.status != PlayerStatus.ELIMINATED:
                player_to_move = player
                source_table.remove_player(player)
                break
        
        if player_to_move is None:
            self.logger.warning("No player found to move")
            return
        
        # Add player to destination table
        dest_table.add_player(player_to_move)
        
        self.logger.info(f"Moved player {player_to_move.name} from {source_table.name} to {dest_table.name}")
    
    def _finish_tournament(self) -> None:
        """Finish the tournament and allocate prizes."""
        if self.status == TournamentStatus.FINISHED:
            return
        
        self.status = TournamentStatus.FINISHED
        
        # Get final standings
        standings = self._get_final_standings()
        
        # Calculate prize pool
        prize_pool = len(self.players) * self.config.buy_in
        
        # Allocate prizes based on payout percentages
        payouts = self._calculate_payouts(prize_pool, len(standings))
        
        self.logger.info(f"Tournament finished. Prize pool: {prize_pool}")
        
        # Assign winnings to players
        for i, (player, position) in enumerate(standings):
            if i < len(payouts):
                player.add_chips(payouts[i])
                self.logger.info(f"{position}. {player.name}: {payouts[i]}")
            else:
                self.logger.info(f"{position}. {player.name}: 0")
    
    def _get_final_standings(self) -> List[Tuple[Player, int]]:
        """
        Get the final tournament standings.
        
        Returns:
            List of (player, position) tuples
        """
        # Start with any remaining active players
        active_players = [p for p in self.players.values() if p.status != PlayerStatus.ELIMINATED]
        
        # Sort active players by chip count (descending)
        active_players.sort(key=lambda p: p.chips, reverse=True)
        
        # Add eliminated players in reverse elimination order
        standings = [(p, i+1) for i, p in enumerate(active_players)]
        
        elim_position = len(active_players) + 1
        for player in reversed(self.eliminated_players):
            standings.append((player, elim_position))
            elim_position += 1
        
        return standings
    
    def _calculate_payouts(self, prize_pool: int, num_players: int) -> List[int]:
        """
        Calculate tournament payouts.
        
        Args:
            prize_pool: Total prize pool
            num_players: Number of players in the tournament
            
        Returns:
            List of payout amounts
        """
        # Determine number of paying positions
        if num_players <= 6:
            num_paying = 1
        elif num_players <= 10:
            num_paying = 2
        elif num_players <= 20:
            num_paying = 3
        elif num_players <= 30:
            num_paying = 4
        elif num_players <= 40:
            num_paying = 5
        else:
            num_paying = max(6, num_players // 7)
        
        # Use configured percentages, or default if not enough
        percentages = self.config.payouts_percentage[:num_paying]
        
        # If percentages don't add up to 100%, adjust them
        total_percentage = sum(percentages)
        if total_percentage != 100.0:
            percentages = [p * 100.0 / total_percentage for p in percentages]
        
        # Calculate actual payouts
        payouts = [int(prize_pool * p / 100.0) for p in percentages]
        
        # Adjust for rounding errors
        remaining = prize_pool - sum(payouts)
        if remaining > 0 and payouts:
            payouts[0] += remaining
        
        return payouts
    
    def get_tournament_status(self) -> Dict[str, Any]:
        """
        Get the current tournament status.
        
        Returns:
            Dictionary with tournament status information
        """
        # Calculate time remaining in current level
        current_time = time.time()
        if self.level_start_time is not None and self.current_level < len(self.config.blind_levels):
            level_duration = self.config.blind_levels[self.current_level].duration_minutes * 60
            elapsed_time = current_time - self.level_start_time
            time_remaining = max(0, level_duration - elapsed_time)
        else:
            time_remaining = 0
        
        # Count active and eliminated players
        active_players = sum(1 for p in self.players.values() if p.status != PlayerStatus.ELIMINATED)
        eliminated_players = len(self.eliminated_players)
        
        return {
            "id": self.id,
            "name": self.config.name,
            "status": self.status.name,
            "start_time": self.start_time,
            "current_level": self.current_level + 1,
            "time_remaining": time_remaining,
            "blinds": self._get_current_blinds().__dict__ if self.status != TournamentStatus.REGISTERING else None,
            "players": {
                "total": len(self.players),
                "active": active_players,
                "eliminated": eliminated_players
            },
            "tables": [{
                "id": table.id,
                "name": table.name,
                "players": table.player_count()
            } for table in self.tables],
            "buy_in": self.config.buy_in,
            "prize_pool": len(self.players) * self.config.buy_in
        }
    
    def get_player_status(self, player_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a specific player.
        
        Args:
            player_id: ID of the player
            
        Returns:
            Dictionary with player status information, or None if player not found
        """
        if player_id not in self.players:
            return None
        
        player = self.players[player_id]
        
        # Find player's table
        table = None
        for t in self.tables:
            for i, seat in enumerate(t.seats):
                if seat is not None and seat.id == player_id:
                    table = t
                    break
            if table:
                break
        
        return {
            "id": player.id,
            "name": player.name,
            "status": player.status.name,
            "chips": player.chips,
            "table": table.name if table else None,
            "position": player.position if player.position >= 0 else None,
            "is_active": player.status != PlayerStatus.ELIMINATED,
        }